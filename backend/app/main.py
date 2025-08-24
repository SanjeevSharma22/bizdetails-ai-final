import os
import csv
import uuid
import re
import json
from io import StringIO, TextIOWrapper
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from passlib.context import CryptContext
from pydantic import BaseModel, Field, root_validator
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_, and_, cast, Integer

import pycountry

from .database import Base, engine, get_db, init_db
from .models import User, CompanyUpdated
from .normalization import normalize_company_name
from .deepseek import fetch_company_data, DeepSeekError

# --- DB bootstrap ---
Base.metadata.create_all(bind=engine)
init_db()


def log_activity(user: User, action: str) -> None:
    """Append a simple activity record to the user's log."""
    events = list(user.activity_log or [])
    events.append({"action": action, "timestamp": datetime.utcnow().isoformat()})
    user.activity_log = events

# --- App ---
app = FastAPI(title="BizDetails AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth / Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "secret")

@AuthJWT.load_config
def get_config():
    return Settings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# --- Schemas ---
class UserSignup(BaseModel):
    email: str
    password: str
    username: Optional[str] = None
    full_name: Optional[str] = Field(None, alias="fullName")
    role: Optional[str] = None

    @root_validator(pre=True)
    def populate_names(cls, values):
        # Accept "name" as an alternative to "fullName" from clients and
        # fall back to using the email when no name is provided.
        if "fullName" not in values:
            if "name" in values:
                values["fullName"] = values["name"]
            elif "username" in values:
                values["fullName"] = values["username"]
            elif "email" in values:
                values["fullName"] = values["email"]
        if "username" not in values and "email" in values:
            values["username"] = values["email"]
        return values

    class Config:
        allow_population_by_field_name = True


class UserCredentials(BaseModel):
    email: str
    password: str

class ProcessRequest(BaseModel):
    data: List[Dict[str, Optional[str]]]
    mapping: Optional[Dict[str, str]] = None  # frontend maps to canonical headers

class ProcessedResult(BaseModel):
    id: int
    companyName: str
    originalData: Dict[str, Optional[str]]
    domain: str
    hq: str
    size: str
    linkedin_url: str
    confidence: str
    matchType: str
    notes: Optional[str]
    country: str
    industry: str
    sources: Dict[str, str] = Field(default_factory=dict)


class FieldStat(BaseModel):
    enriched: int = 0
    internal: int = 0
    ai: int = 0


class JobMeta(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    total_records: int
    processed_records: int
    internal_fields: int
    ai_fields: int
    field_stats: Dict[str, FieldStat]
    file_name: Optional[str] = None


class JobData(BaseModel):
    meta: JobMeta
    results: List[ProcessedResult]

# Response schema for dashboard company listings
class CompanyOut(BaseModel):
    id: int
    name: Optional[str]
    domain: str
    hq: Optional[str]
    size: Optional[str]
    industry: Optional[str]
    linkedin_url: Optional[str]

    class Config:
        orm_mode = True

# In-memory task store (MVP)
TASK_RESULTS: Dict[str, List[ProcessedResult]] = {}
JOB_STORE: Dict[str, JobData] = {}

# --- Normalization helpers ---

def normalize_domain(domain: str) -> str:
    """Return the root domain without protocol, www, or paths."""
    if not domain:
        return ""
    domain = domain.strip().lower()
    if not domain:
        return ""
    if not re.match(r"^https?://", domain):
        domain = "http://" + domain
    parsed = urlparse(domain)
    host = parsed.netloc or parsed.path
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def extract_linkedin_slug(url: str) -> str:
    """Isolate the company slug from a LinkedIn URL."""
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url):
        url = "https://" + url
    parsed = urlparse(url)
    path = parsed.path.lower()
    match = re.search(r"/company/([^/]+)/?", path)
    if match:
        return match.group(1)
    # If no /company/ segment, assume provided slug
    return path.strip("/")


def process_job_rows(
    rows: List[Dict[str, Optional[str]]], db: Session
) -> tuple[List[ProcessedResult], Dict[str, FieldStat], int, int]:
    results: List[ProcessedResult] = []
    fields = [
        "companyName",
        "domain",
        "hq",
        "size",
        "linkedin_url",
        "country",
        "industry",
    ]
    field_stats = {name: FieldStat() for name in fields}
    internal_total = 0
    ai_total = 0

    for idx, row in enumerate(rows, start=1):
        name = row.get("company_name") or row.get("Company Name") or ""
        domain = row.get("domain") or row.get("Domain") or ""
        linkedin = row.get("linkedin_url") or row.get("LinkedIn URL") or ""
        norm_domain = normalize_domain(domain)
        sources: Dict[str, str] = {}
        data: Dict[str, Any] = {
            "companyName": name,
            "domain": norm_domain,
            "hq": "",
            "size": "",
            "linkedin_url": linkedin,
            "country": "",
            "industry": "",
        }
        company = None
        if norm_domain:
            company = (
                db.query(CompanyUpdated)
                .filter(func.lower(CompanyUpdated.domain) == norm_domain)
                .first()
            )
        if company:
            data["companyName"] = company.name or name
            data["domain"] = company.domain or norm_domain
            data["hq"] = company.hq or ""
            data["size"] = company.size or ""
            data["linkedin_url"] = company.linkedin_url or ""
            data["industry"] = company.industry or ""
            data["country"] = (
                company.countries[0] if getattr(company, "countries", None) else ""
            )
            for f in fields:
                if data.get(f):
                    sources[f] = "internal"
                    field_stats[f].enriched += 1
                    field_stats[f].internal += 1
                    internal_total += 1
        else:
            try:
                fetched = fetch_company_data(
                    name=name or None, domain=norm_domain or None, linkedin_url=linkedin or None
                )
                data["companyName"] = fetched.get("name") or name
                data["domain"] = fetched.get("domain") or norm_domain
                data["hq"] = fetched.get("hq") or ""
                data["size"] = fetched.get("size") or ""
                data["linkedin_url"] = fetched.get("linkedin_url") or ""
                data["industry"] = fetched.get("industry") or ""
                countries = fetched.get("countries") or []
                data["country"] = countries[0] if countries else ""
                for f in fields:
                    if data.get(f):
                        sources[f] = "ai"
                        field_stats[f].enriched += 1
                        field_stats[f].ai += 1
                        ai_total += 1
            except DeepSeekError:
                pass

        result = ProcessedResult(
            id=idx,
            companyName=data["companyName"],
            originalData=row,
            domain=data["domain"],
            hq=data["hq"],
            size=data["size"],
            linkedin_url=data["linkedin_url"],
            confidence="High" if sources else "Low",
            matchType="Internal" if company else ("AI" if sources else "None"),
            notes=None if sources else "Not found",
            country=data["country"],
            industry=data["industry"],
            sources=sources,
        )
        results.append(result)

    return results, field_stats, internal_total, ai_total

# --- Enrichment ---
def enrich_domains(
    data: List[Dict[str, Optional[str]]], db: Session
) -> List[ProcessedResult]:
    results: List[ProcessedResult] = []

    for idx, row in enumerate(data, start=1):
        domain = normalize_domain(row.get("Domain") or "")
        linkedin_slug = extract_linkedin_slug(row.get("LinkedIn URL") or "")
        original_name = row.get("Company Name") or ""
        company = None
        match_type = "None"
        note = None

        # 1) Exact domain match (case-insensitive)
        if domain:
            company = (
                db.query(CompanyUpdated)
                .filter(func.lower(CompanyUpdated.domain) == domain)
                .first()
            )
            if company:
                match_type = "Exact"
            else:
                note = "Domain not found"

        # 2) LinkedIn URL slug match
        if not company and linkedin_slug:
            candidates = (
                db.query(CompanyUpdated)
                .filter(CompanyUpdated.linkedin_url != None)
                .all()
            )
            for c in candidates:
                if extract_linkedin_slug(c.linkedin_url or "").lower() == linkedin_slug:
                    company = c
                    match_type = "LinkedIn URL" if not domain else "Domain+LinkedIn URL"
                    break
            if not company:
                note = note or "LinkedIn URL not found"

        # 3) Fallback: company-name match with optional filters
        if not company:
            name = normalize_company_name(original_name).lower()
            if name:
                query = db.query(CompanyUpdated).filter(
                    func.lower(CompanyUpdated.name) == name
                )

                country = (row.get("Country") or "").strip()
                if country:
                    # CompanyUpdated.countries is expected to be ARRAY of ISO alpha-2 (e.g., "IN", "US")
                    query = query.filter(CompanyUpdated.countries.any(country.upper()))

                industry = (row.get("Industry") or "").strip()
                if industry:
                    query = query.filter(
                        func.lower(CompanyUpdated.industry) == industry.lower()
                    )

                subindustry = (row.get("Subindustry") or "").strip()
                if subindustry:
                    query = query.filter(
                        func.lower(CompanyUpdated.subindustry) == subindustry.lower()
                    )

                size = (row.get("Company Size") or "").strip()
                if size:
                    query = query.filter(func.lower(CompanyUpdated.size) == size.lower())

                keywords = (row.get("Keywords") or "").strip()
                if keywords:
                    # If your source is CSV of terms, split and OR them.
                    # For now, simple ANY on the full string.
                    query = query.filter(CompanyUpdated.keywords_cntxt.any(keywords))

                company = query.first()
                if company:
                    if domain:
                        match_type = "Domain+Company Name"
                    elif linkedin_slug:
                        match_type = "LinkedIn URL+Company Name"
                    else:
                        match_type = "Company Name"
                else:
                    note = note or "Company not found"
            else:
                note = note or (
                    "Domain not found"
                    if domain or linkedin_slug
                    else "Company not found"
                )

        if company:
            result_country = (
                company.countries[0] if getattr(company, "countries", None) else ""
            )
            results.append(
                ProcessedResult(
                    id=idx,
                    companyName=company.name or original_name,
                    originalData=row,
                    domain=company.domain or domain,
                    hq=company.hq or "",
                    size=company.size or "",
                    linkedin_url=company.linkedin_url or "",
                    confidence="High",
                    matchType=match_type,
                    notes=None,
                    country=result_country,
                    industry=company.industry or "",
                )
            )
        else:
            results.append(
                ProcessedResult(
                    id=idx,
                    companyName=original_name,
                    originalData=row,
                    domain=domain,
                    hq=row.get("HQ") or "",
                    size=row.get("Company Size") or row.get("Size") or "",
                    linkedin_url=row.get("LinkedIn URL") or "",
                    confidence="Low",
                    matchType="None",
                    notes=note or "Not found",
                    country=row.get("Country") or "",
                    industry=row.get("Industry") or "",
                )
            )
    return results

# --- Preprocessing helpers (optional) ---
INDUSTRY_TAXONOMY = {
    "technology": "Technology",
    "tech": "Technology",
    "finance": "Finance",
    "financial services": "Finance",
    "healthcare": "Healthcare",
}

def normalize_country(country: Optional[str]) -> Optional[str]:
    if not country:
        return None
    country = country.strip()
    if len(country) == 2 and country.isalpha():
        try:
            return pycountry.countries.get(alpha_2=country.upper()).alpha_2
        except AttributeError:
            return None
    try:
        return pycountry.countries.search_fuzzy(country)[0].alpha_2
    except LookupError:
        return None

def normalize_industry(industry: Optional[str]) -> Optional[str]:
    if not industry:
        return None
    return INDUSTRY_TAXONOMY.get(industry.strip().lower())

def normalize_subindustry(subindustry: Optional[str]) -> Optional[str]:
    if not subindustry:
        return None  # replace with real taxonomy when available
    return INDUSTRY_TAXONOMY.get(subindustry.strip().lower())

def preprocess_rows(rows: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    cleaned: List[Dict[str, Optional[str]]] = []
    seen = set()
    for row in rows:
        original_name = row.get("Company Name") or ""
        if not original_name.strip():
            raise HTTPException(status_code=400, detail="Company Name is required")
        name = normalize_company_name(original_name)
        country = normalize_country(row.get("Country"))
        industry = normalize_industry(row.get("Industry"))
        subindustry = normalize_subindustry(row.get("Subindustry"))
        company_size = row.get("Company Size")
        keywords = row.get("Keywords")

        identifier = (
            name.lower(),
            country,
            industry,
            subindustry,
            company_size,
            keywords,
        )
        if identifier in seen:
            continue
        seen.add(identifier)

        cleaned.append(
            {
                "Company Name": name,
                "Country": country,
                "Industry": industry,
                "Subindustry": subindustry,
                "Company Size": company_size,
                "Keywords": keywords,
            }
        )
    return cleaned

# --- Auth Endpoints ---
@app.post("/api/auth/signup")
def signup(
    credentials: UserSignup,
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    if db.query(User).filter(User.email == credentials.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == credentials.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(credentials.password)
    user = User(
        email=credentials.email,
        username=credentials.username,
        hashed_password=hashed_password,
        full_name=credentials.full_name or credentials.email,
        role=credentials.role or "User",
        activity_log=[{"action": "signup", "timestamp": datetime.utcnow().isoformat()}],
    )
    db.add(user)
    db.commit()
    access_token = authorize.create_access_token(subject=user.email)
    return {"access_token": access_token}

@app.post("/api/auth/signin")
def signin(
    credentials: UserCredentials,
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.last_login = datetime.utcnow()
    log_activity(user, "signin")
    db.commit()
    access_token = authorize.create_access_token(subject=user.email)
    return {"access_token": access_token}

@app.get("/api/auth/verify")
def verify_token(authorize: AuthJWT = Depends()):
    try:
        authorize.jwt_required()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    current_user = authorize.get_jwt_subject()
    return {"email": current_user}

# --- Upload & Processing ---
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    # utf-8-sig strips BOM if present
    text = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.reader(StringIO(text))
    headers = next(reader, [])
    return {"headers": headers}

@app.post("/api/process")
async def process(
    req: ProcessRequest,
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    authorize.jwt_required()
    current_user_email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == current_user_email).first()

    rows = req.data or []

    # Apply mapping from frontend (maps arbitrary column names to expected keys)
    if req.mapping:
        mapped_rows: List[Dict[str, Optional[str]]] = []
        for row in rows:
            mapped_row: Dict[str, Optional[str]] = {}
            for field, col in req.mapping.items():
                mapped_row[field] = row.get(col)
            mapped_rows.append(mapped_row)
        rows = mapped_rows

    # Filter out rows missing key identifiers rather than failing the request
    filtered_rows: List[Dict[str, Optional[str]]] = []
    for row in rows:
        has_domain = (row.get("Domain") or "").strip()
        has_name = (row.get("Company Name") or "").strip()
        has_linkedin = (row.get("LinkedIn URL") or "").strip()
        if not (has_domain or has_name or has_linkedin):
            continue
        filtered_rows.append(row)
    rows = filtered_rows

    enriched = enrich_domains(rows, db)
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = enriched
    if user:
        user.enrichment_count += 1
        user.last_enrichment_at = datetime.utcnow()
        log_activity(user, "enrichment")
        db.commit()
    return {"task_id": task_id}

@app.get("/api/results")
async def get_results(task_id: str):
    """Return processed results for a given task id."""
    return {"results": [r.dict() for r in TASK_RESULTS.get(task_id, [])]}


class SaveResultsRequest(BaseModel):
    results: List[ProcessedResult]


@app.post("/api/save_results")
async def save_results(req: SaveResultsRequest):
    """Persist enriched results for the user's account (placeholder)."""
    TASK_RESULTS.setdefault("saved", []).extend(req.results)
    return {"saved": len(req.results)}

@app.get("/api/results/{task_id}/status")
async def task_status(task_id: str):
    status = "completed" if task_id in TASK_RESULTS else "pending"
    return {"task_id": task_id, "status": status}


@app.post("/api/jobs")
async def create_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    authorize.jwt_required()
    text = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(StringIO(text))
    headers = [h.lower() for h in (reader.fieldnames or [])]
    if "company_name" not in headers or "domain" not in headers:
        raise HTTPException(
            status_code=400,
            detail="CSV must include company_name and domain columns",
        )
    rows = [row for row in reader]
    if len(rows) > 10000:
        raise HTTPException(status_code=400, detail="CSV exceeds 10000 rows")
    seen = set()
    deduped = []
    for row in rows:
        d = (row.get("domain") or "").lower()
        if d in seen:
            continue
        seen.add(d)
        deduped.append(row)
    results, stats, internal_total, ai_total = process_job_rows(
        deduped, db
    )
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    meta = JobMeta(
        job_id=job_id,
        status="completed",
        created_at=now,
        updated_at=now,
        total_records=len(deduped),
        processed_records=len(deduped),
        internal_fields=internal_total,
        ai_fields=ai_total,
        field_stats=stats,
        file_name=file.filename,
    )
    JOB_STORE[job_id] = JobData(meta=meta, results=results)
    current_user_email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == current_user_email).first()
    if user:
        user.enrichment_count += 1
        user.last_enrichment_at = datetime.utcnow()
        log_activity(user, "job_enrichment")
        db.commit()
    return {"job_id": job_id}


@app.get("/api/jobs")
def list_jobs():
    jobs = []
    for job_id, data in JOB_STORE.items():
        meta = data.meta
        total = meta.internal_fields + meta.ai_fields
        internal_pct = (meta.internal_fields / total * 100) if total else 0.0
        ai_pct = (meta.ai_fields / total * 100) if total else 0.0
        progress = (
            meta.processed_records / meta.total_records * 100
            if meta.total_records
            else 0.0
        )
        jobs.append(
            {
                "job_id": job_id,
                "status": meta.status,
                "progress": progress,
                "created_at": meta.created_at,
                "updated_at": meta.updated_at,
                "internal_pct": internal_pct,
                "ai_pct": ai_pct,
            }
        )
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}")
def job_details(job_id: str):
    data = JOB_STORE.get(job_id)
    if not data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "meta": data.meta.dict(),
        "results": [r.dict() for r in data.results],
    }


@app.get("/api/company", response_model=CompanyOut)
def get_company(domain: str = Query(...), db: Session = Depends(get_db)):
    """Retrieve a company, falling back to DeepSeek API if missing."""
    norm_domain = normalize_domain(domain)
    company = (
        db.query(CompanyUpdated)
        .filter(func.lower(CompanyUpdated.domain) == norm_domain.lower())
        .first()
    )
    if company:
        return CompanyOut.from_orm(company)

    try:
        data = fetch_company_data(domain=norm_domain)
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    company = CompanyUpdated(
        name=data.get("name"),
        domain=norm_domain,
        hq=data.get("hq"),
        size=data.get("size"),
        industry=data.get("industry"),
        linkedin_url=data.get("linkedin_url"),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyOut.from_orm(company)

@app.get("/api/company_updated")
def list_company_updated(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_key: str = "name",
    sort_dir: str = "asc",
    company_name: Optional[str] = None,
    domain: Optional[str] = None,
    hq: Optional[str] = None,
    size_min: Optional[int] = Query(None, ge=0),
    size_max: Optional[int] = Query(None, ge=0),
    size_range: List[str] = Query([]),
    db: Session = Depends(get_db),
):
    """Return CompanyUpdated records with pagination."""
    query = db.query(CompanyUpdated)

    if search:
        pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(CompanyUpdated.name).like(pattern),
                func.lower(CompanyUpdated.domain).like(pattern),
                func.lower(CompanyUpdated.industry).like(pattern),
                func.lower(CompanyUpdated.hq).like(pattern),
            )
        )

    if company_name:
        query = query.filter(
            func.lower(CompanyUpdated.name).like(f"%{company_name.lower()}%")
        )

    if domain:
        norm_domain = normalize_domain(domain)
        query = query.filter(func.lower(CompanyUpdated.domain) == norm_domain.lower())

    if hq:
        query = query.filter(func.lower(CompanyUpdated.hq).like(f"%{hq.lower()}%"))

    if size_range:
        size_col = cast(CompanyUpdated.size, Integer)
        range_map = {
            "1-10": (1, 10),
            "11-50": (11, 50),
            "51-200": (51, 200),
            "201-500": (201, 500),
            "501-1000": (501, 1000),
            "1001-5000": (1001, 5000),
            "5001-10,000": (5001, 10000),
            "10,001+": (10001, None),
        }
        filters = []
        for label in size_range:
            rng = range_map.get(label)
            if not rng:
                continue
            min_v, max_v = rng
            cond = size_col >= min_v
            if max_v is not None:
                cond = and_(cond, size_col <= max_v)
            filters.append(cond)
        if filters:
            query = query.filter(or_(*filters))

    if size_min is not None:
        query = query.filter(cast(CompanyUpdated.size, Integer) >= size_min)
    if size_max is not None:
        query = query.filter(cast(CompanyUpdated.size, Integer) <= size_max)

    if sort_key not in {"name", "domain", "hq", "industry", "size"}:
        sort_key = "name"
    if sort_key == "size":
        sort_column = cast(CompanyUpdated.size, Integer)
    else:
        sort_column = getattr(CompanyUpdated, sort_key)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    total = query.count()
    companies = (
        query.offset((page - 1) * page_size).limit(page_size).all()
    )
    return {
        "companies": [CompanyOut.from_orm(c).dict() for c in companies],
        "total": total,
    }

@app.get("/api/dashboard")
def dashboard(authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    authorize.jwt_required()
    email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    last_job = None
    if JOB_STORE:
        latest = max(JOB_STORE.values(), key=lambda j: j.meta.created_at)
        last_meta = latest.meta
        last_job = {
            "file_name": last_meta.file_name,
            "total_records": last_meta.total_records,
            "processed_records": last_meta.processed_records,
        }
    return {
        "stats": {
            "enrichment_count": user.enrichment_count,
            "last_login": user.last_login,
            "last_enrichment_at": user.last_enrichment_at,
            "activity_log": user.activity_log or [],
            "last_job": last_job,
        }
    }

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    return {"response": "Chat endpoint not implemented."}


@app.post("/api/admin/company-updated/upload")
async def admin_company_upload(
    file: UploadFile = File(...),
    mode: str = Form(...),
    column_map: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    """Allow admins to bulk upsert CompanyUpdated records via CSV.

    ``mode`` controls how conflicts are resolved:

    * ``override`` – Non-empty CSV values replace existing data.
    * ``missing`` – Only populate fields that are empty in the DB.
    """

    authorize.jwt_required()
    current_email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == current_email).first()
    if not user or user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    mode = mode.lower()
    if mode not in {"override", "missing"}:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Ensure the primary key sequence is aligned (especially for PostgreSQL)
    if db.bind.dialect.name == "postgresql":
        db.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('company_updated','id'), "
                "COALESCE((SELECT MAX(id) FROM company_updated), 0) + 1, false)"
            )
        )
        db.commit()

    # Stream file content instead of loading entire file into memory
    file.file.seek(0)
    text_stream = TextIOWrapper(
        file.file, encoding="utf-8-sig", errors="ignore"
    )
    reader = csv.DictReader(text_stream)

    # Normalize CSV headers by stripping whitespace and lowering case
    raw_headers = reader.fieldnames or []
    normalized_headers = [h.strip().lower() for h in raw_headers if h is not None]
    reader.fieldnames = normalized_headers

    mapping = {}
    if column_map:
        try:
            mapping = json.loads(column_map)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid column_map")
        # Normalize mapping to match sanitized headers
        mapping = {
            k.lower(): v.strip().lower() for k, v in mapping.items() if isinstance(v, str)
        }

    required = {"domain"}
    _optional = {
        "name",
        "countries",
        "hq",
        "industry",
        "subindustry",
        "keywords_cntxt",
        "size",
        "linkedin_url",
        "slug",
        "original_name",
        "legal_name",
    }

    headers = set(normalized_headers)
    missing_required = {
        field
        for field in required
        if mapping.get(field, field) not in headers
    }
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {', '.join(sorted(missing_required))}",
        )

    created = 0
    updated = 0
    errors = []

    for idx, row in enumerate(reader, start=1):
        try:
            def get(field: str):
                return row.get(mapping.get(field, field))

            domain = (get("domain") or "").strip().lower()
            if not domain:
                raise ValueError("Invalid domain provided")

            linkedin_url = (get("linkedin_url") or "").strip()
            if linkedin_url:
                parsed = urlparse(linkedin_url if re.match(r"^https?://", linkedin_url) else "https://" + linkedin_url)
                if not parsed.netloc:
                    raise ValueError("Malformed LinkedIn URL")

            def clean(val):
                return (val or "").strip() or None

            countries = [
                c.strip() for c in (get("countries") or "").split(",") if c.strip()
            ]
            keywords = [
                k.strip() for k in (get("keywords_cntxt") or "").split(",") if k.strip()
            ]
            data_fields = {
                "name": clean(get("name")),
                "countries": countries or None,
                "hq": clean(get("hq")),
                "industry": clean(get("industry")),
                "subindustry": clean(get("subindustry")),
                "keywords_cntxt": keywords or None,
                "size": clean(get("size")),
                "linkedin_url": clean(linkedin_url),
                "slug": clean(get("slug")),
                "original_name": clean(get("original_name")),
                "legal_name": clean(get("legal_name")),
            }

            entry = (
                db.query(CompanyUpdated)
                .filter(func.lower(CompanyUpdated.domain) == domain)
                .first()
            )

            if entry:
                changed = False
                for field, value in data_fields.items():
                    if mode == "override":
                        if value not in (None, "", []):
                            setattr(entry, field, value)
                            changed = True
                    else:  # mode == 'missing'
                        current = getattr(entry, field)
                        is_empty = current in (None, "", []) or (
                            isinstance(current, list) and len(current) == 0
                        )
                        if is_empty and value not in (None, "", []):
                            setattr(entry, field, value)
                            changed = True
                if changed:
                    updated += 1
            else:
                entry = CompanyUpdated(domain=domain, **data_fields)
                db.add(entry)
                created += 1

            db.commit()
        except Exception as e:
            db.rollback()
            errors.append({"row": idx, "error": str(e)})

    # Record this upload as an enrichment action for dashboard stats
    if user:
        user.enrichment_count += 1
        user.last_enrichment_at = datetime.utcnow()
        log_activity(user, "admin_upload")
        db.commit()

    return {"created": created, "updated": updated, "errors": errors}
