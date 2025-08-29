import os
import csv
import uuid
import re
import json
import logging
from io import StringIO, TextIOWrapper
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from passlib.context import CryptContext
from pydantic import BaseModel, Field, root_validator
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_, and_, cast, String

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
    events.append({"action": action, "timestamp": datetime.now(timezone.utc).isoformat()})
    # Keep only the 10 most recent activities to prevent unbounded growth
    if len(events) > 10:
        events = events[-10:]
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
    file_name: Optional[str] = None

class ProcessedResult(BaseModel):
    id: int
    companyName: str
    originalData: Dict[str, Optional[str]]
    domain: str
    hq: str
    size: Optional[int]
    employee_range: Optional[str]
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

# --- Employee size helpers ---

def employee_range_from_size(size: Optional[int]) -> Optional[str]:
    """Map an exact employee count to a human-readable range."""
    if size is None:
        return None
    ranges = [
        (1, 10, "1-10"),
        (11, 50, "11-50"),
        (51, 200, "51-200"),
        (201, 500, "201-500"),
        (501, 1000, "501-1,000"),
        (1001, 5000, "1,001-5,000"),
        (5001, 10000, "5,001-10,000"),
        (10001, None, "10,001+"),
    ]
    for min_v, max_v, label in ranges:
        if size >= min_v and (max_v is None or size <= max_v):
            return label
    return None

# Response schema for dashboard company listings
class CompanyOut(BaseModel):
    id: int
    name: Optional[str]
    domain: str
    hq: Optional[str]
    size: Optional[int]
    employee_range: Optional[str]
    industry: Optional[str]
    linkedin_url: Optional[str]

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def compute_range(cls, values):
        data = dict(values)
        if not data.get("employee_range") and data.get("size") is not None:
            data["employee_range"] = employee_range_from_size(data.get("size"))
        return data

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


def parse_employee_size(value: Optional[str]) -> tuple[Optional[int], Optional[str]]:
    """Split a raw size string into either an integer or a range string."""
    if not value:
        return None, None
    cleaned = value.replace(",", "").strip()
    if cleaned.isdigit():
        size_int = int(cleaned)
        return size_int, employee_range_from_size(size_int)
    return None, cleaned or None


def first_country(countries: Optional[Any]) -> str:
    """Return the first country from a list or the string itself.

    ``CompanyUpdated.countries`` is defined as an ARRAY for PostgreSQL but tests use
    SQLite where the column is a plain string. Attempting to index into a string
    returns a single character, so this helper normalizes both cases.
    """
    if not countries:
        return ""
    if isinstance(countries, list):
        return countries[0] if countries else ""
    return str(countries)


def process_job_rows(
    rows: List[Dict[str, Optional[str]]],
    db: Session,
    user: Optional[User] = None,
    file_name: Optional[str] = None,
) -> tuple[List[ProcessedResult], Dict[str, FieldStat], int, int]:
    results: List[ProcessedResult] = []
    fields = [
        "companyName",
        "domain",
        "hq",
        "size",
        "employee_range",
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
            "size": None,
            "employee_range": None,
            "linkedin_url": linkedin,
            "country": "",
            "industry": "",
        }
        company = None
        note: Optional[str] = None
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
            data["size"] = company.size
            size_range = company.employee_range or employee_range_from_size(company.size)
            data["employee_range"] = size_range
            company.uploaded_by = user.id if user else None
            company.source_file_name = file_name
            if company.employee_range != size_range and size_range is not None:
                company.employee_range = size_range
            try:
                db.commit()
            except Exception as exc:
                logger.warning("Failed to update company info: %s", exc)
                db.rollback()
            data["linkedin_url"] = company.linkedin_url or ""
            data["industry"] = company.industry or ""
            data["country"] = first_country(getattr(company, "countries", None))
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
                raw_size = fetched.get("size") or ""
                size_int, size_range = parse_employee_size(raw_size)
                size_range = size_range or employee_range_from_size(size_int)
                data["size"] = size_int
                data["employee_range"] = size_range
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

                # Persist new record for future use
                record_domain = data.get("domain")
                if record_domain:
                    exists = (
                        db.query(CompanyUpdated)
                        .filter(func.lower(CompanyUpdated.domain) == record_domain.lower())
                        .first()
                    )
                    if not exists:
                        db.add(
                            CompanyUpdated(
                                name=data.get("companyName"),
                                domain=record_domain,
                                hq=data.get("hq") or None,
                                size=data.get("size"),
                                employee_range=data.get("employee_range"),
                                industry=data.get("industry") or None,
                                linkedin_url=data.get("linkedin_url") or None,
                                uploaded_by=user.id if user else None,
                                source_file_name=file_name,
                            )
                        )
                        try:
                            db.commit()
                        except Exception as exc:
                            logger.warning("Failed to persist DeepSeek record: %s", exc)
                            db.rollback()
            except DeepSeekError as exc:
                note = f"DeepSeek enrichment failed: {exc}"
                logger.warning("DeepSeek enrichment failed: %s", exc)

        result = ProcessedResult(
            id=idx,
            companyName=data["companyName"],
            originalData=row,
            domain=data["domain"],
            hq=data["hq"],
            size=data["size"],
            employee_range=data["employee_range"],
            linkedin_url=data["linkedin_url"],
            confidence="High" if sources else "Low",
            matchType="Internal" if company else ("AI" if sources else "None"),
            notes=note if note is not None else (None if sources else "Not found"),
            country=data["country"],
            industry=data["industry"],
            sources=sources,
        )
        results.append(result)

    return results, field_stats, internal_total, ai_total

# --- Enrichment ---
def enrich_domains(
    data: List[Dict[str, Optional[str]]],
    db: Session,
    user: Optional[User] = None,
    file_name: Optional[str] = None,
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
                    # Support both ARRAY (PostgreSQL) and plain string (SQLite) columns.
                    query = query.filter(
                        cast(CompanyUpdated.countries, String).ilike(f"%{country}%")
                    )

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

                size_str = (row.get("Company Size") or "").strip()
                if size_str:
                    size_int, size_range = parse_employee_size(size_str)
                    if size_int is not None:
                        query = query.filter(CompanyUpdated.size == size_int)
                    elif size_range:
                        query = query.filter(CompanyUpdated.employee_range == size_range)

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
            result_country = first_country(getattr(company, "countries", None))
            size_range = company.employee_range or employee_range_from_size(company.size)
            company.uploaded_by = user.id if user else None
            company.source_file_name = file_name
            if company.employee_range != size_range and size_range is not None:
                company.employee_range = size_range
            try:
                db.commit()
            except Exception as exc:
                logger.warning("Failed to update company info: %s", exc)
                db.rollback()
            results.append(
                ProcessedResult(
                    id=idx,
                    companyName=company.name or original_name,
                    originalData=row,
                    domain=company.domain or domain,
                    hq=company.hq or "",
                    size=company.size,
                    employee_range=size_range,
                    linkedin_url=company.linkedin_url or "",
                    confidence="High",
                    matchType=match_type,
                    notes=None,
                    country=result_country,
                    industry=company.industry or "",
                )
            )
        else:
            try:
                fetched = fetch_company_data(
                    name=original_name or None,
                    domain=domain or None,
                    linkedin_url=row.get("LinkedIn URL") or None,
                )

                company_name = fetched.get("name") or original_name
                fetched_domain = normalize_domain(fetched.get("domain") or domain)
                hq = fetched.get("hq") or (row.get("HQ") or "")
                raw_size = fetched.get("size") or (
                    row.get("Company Size") or row.get("Size") or ""
                )
                size_int, size_range = parse_employee_size(raw_size)
                linkedin_url = fetched.get("linkedin_url") or (
                    row.get("LinkedIn URL") or ""
                )
                industry = fetched.get("industry") or (row.get("Industry") or "")
                countries = fetched.get("countries") or []
                country = countries[0] if countries else (row.get("Country") or "")

                sources: Dict[str, str] = {}
                for field, value in {
                    "companyName": company_name,
                    "domain": fetched_domain,
                    "hq": hq,
                    "size": size_int,
                    "employee_range": size_range,
                    "linkedin_url": linkedin_url,
                    "industry": industry,
                    "country": country,
                }.items():
                    if value:
                        sources[field] = "ai"

                if fetched_domain:
                    exists = (
                        db.query(CompanyUpdated)
                        .filter(func.lower(CompanyUpdated.domain) == fetched_domain.lower())
                        .first()
                    )
                    if not exists:
                        db.add(
                            CompanyUpdated(
                                name=company_name,
                                domain=fetched_domain,
                                hq=hq or None,
                                size=size_int,
                                employee_range=size_range,
                                industry=industry or None,
                                linkedin_url=linkedin_url or None,
                                uploaded_by=user.id if user else None,
                                source_file_name=file_name,
                            )
                        )
                        try:
                            db.commit()
                        except Exception as exc:
                            logger.warning("Failed to persist DeepSeek record: %s", exc)
                            db.rollback()

                if sources:
                    results.append(
                        ProcessedResult(
                            id=idx,
                            companyName=company_name,
                            originalData=row,
                            domain=fetched_domain,
                            hq=hq,
                            size=size_int,
                            employee_range=size_range,
                            linkedin_url=linkedin_url,
                            confidence="High",
                            matchType="AI",
                            notes=None,
                            country=country,
                            industry=industry,
                            sources=sources,
                        )
                    )
                    continue
            except DeepSeekError as exc:
                logger.warning("DeepSeek enrichment failed: %s", exc)

            raw_size = row.get("Company Size") or row.get("Size") or ""
            size_int, size_range = parse_employee_size(raw_size)
            results.append(
                ProcessedResult(
                    id=idx,
                    companyName=original_name,
                    originalData=row,
                    domain=domain,
                    hq=row.get("HQ") or "",
                    size=size_int,
                    employee_range=size_range,
                    linkedin_url=row.get("LinkedIn URL") or "",
                    confidence="Low",
                    matchType="None",
                    notes=note or "Not found",
                    country=row.get("Country") or "",
                    industry=row.get("Industry") or "",
                )
            )
    return results

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
        activity_log=[{"action": "signup", "timestamp": datetime.now(timezone.utc).isoformat()}],
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
    user.last_login = datetime.now(timezone.utc)
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

    enriched = enrich_domains(rows, db, user=user, file_name=req.file_name)
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = enriched
    if user:
        user.enrichment_count += 1
        user.last_enrichment_at = datetime.now(timezone.utc)
        if req.file_name:
            user.last_file_name = req.file_name
        user.last_accounts_pushed = len(rows)
        user.last_accounts_enriched = len(enriched)
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
    current_user_email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == current_user_email).first()
    results, stats, internal_total, ai_total = process_job_rows(
        deduped, db, user=user, file_name=file.filename
    )
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
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
    if user:
        user.enrichment_count += 1
        user.last_enrichment_at = datetime.now(timezone.utc)
        user.last_file_name = file.filename
        user.last_accounts_pushed = len(deduped)
        user.last_accounts_enriched = len(deduped)
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
def get_company(
    domain: Optional[str] = None,
    name: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    subindustry: Optional[str] = None,
    size: Optional[str] = None,
    keywords: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve a company, falling back to DeepSeek API if missing."""
    if not any([domain, name, linkedin_url]):
        raise HTTPException(
            status_code=400,
            detail="One of 'domain', 'name', or 'linkedin_url' is required",
        )

    norm_domain = normalize_domain(domain) if domain else ""
    slug = extract_linkedin_slug(linkedin_url) if linkedin_url else ""
    keyword_list = [k.strip() for k in (keywords or "").split(",") if k.strip()] or None

    company = None
    if slug:
        company = (
            db.query(CompanyUpdated)
            .filter(func.lower(CompanyUpdated.slug) == slug.lower())
            .first()
        )
    if not company and norm_domain:
        company = (
            db.query(CompanyUpdated)
            .filter(func.lower(CompanyUpdated.domain) == norm_domain.lower())
            .first()
        )
    if not company and name:
        query = db.query(CompanyUpdated).filter(
            func.lower(CompanyUpdated.name) == name.lower()
        )
        if country:
            query = query.filter(
                cast(CompanyUpdated.countries, String).ilike(f"%{country}%")
            )
        if industry:
            query = query.filter(func.lower(CompanyUpdated.industry) == industry.lower())
        if subindustry:
            query = query.filter(
                func.lower(CompanyUpdated.subindustry) == subindustry.lower()
            )
        if size:
            try:
                size_int = int(re.sub(r"\D", "", size))
                query = query.filter(CompanyUpdated.size == size_int)
            except ValueError:
                pass
        if keyword_list:
            for kw in keyword_list:
                query = query.filter(
                    cast(CompanyUpdated.keywords_cntxt, String).ilike(f"%{kw}%")
                )
        company = query.first()
    if company:
        return CompanyOut.from_orm(company)

    try:
        data = fetch_company_data(
            name=name,
            domain=norm_domain or None,
            linkedin_url=linkedin_url,
            country=country,
            industry=industry,
            subindustry=subindustry,
            size=size,
            keywords=keyword_list,
        )
    except DeepSeekError as exc:
        logger.warning("DeepSeek enrichment failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    raw_size = data.get("size")
    size_int, size_range = parse_employee_size(raw_size)
    size_range = size_range or employee_range_from_size(size_int)
    domain_val = normalize_domain(data.get("domain")) or norm_domain
    countries_val = data.get("countries") or ([country] if country else None)
    keywords_val = data.get("keywords_cntxt") or keyword_list
    if db.bind.dialect.name == "sqlite":
        countries_val = None
        keywords_val = None
    company = CompanyUpdated(
        name=data.get("name") or name,
        domain=domain_val,
        countries=countries_val,
        hq=data.get("hq"),
        industry=data.get("industry") or industry,
        subindustry=(data.get("subindustries") or [subindustry or None])[0],
        keywords_cntxt=keywords_val,
        size=size_int,
        employee_range=size_range,
        linkedin_url=data.get("linkedin_url") or linkedin_url,
        slug=data.get("slug") or slug,
        original_name=data.get("original_name"),
        legal_name=data.get("legal_name"),
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
            conds = [CompanyUpdated.employee_range == label]
            if rng:
                min_v, max_v = rng
                c = CompanyUpdated.size >= min_v
                if max_v is not None:
                    c = and_(c, CompanyUpdated.size <= max_v)
                conds.append(c)
            filters.append(or_(*conds))
        if filters:
            query = query.filter(or_(*filters))

    if size_min is not None:
        query = query.filter(CompanyUpdated.size >= size_min)
    if size_max is not None:
        query = query.filter(CompanyUpdated.size <= size_max)

    if sort_key not in {"name", "domain", "hq", "industry", "size"}:
        sort_key = "name"
    if sort_key == "size":
        sort_column = CompanyUpdated.size
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
    if (
        user.last_file_name
        or user.last_accounts_pushed
        or user.last_accounts_enriched
    ):
        last_job = {
            "file_name": user.last_file_name,
            "total_records": user.last_accounts_pushed,
            "processed_records": user.last_accounts_enriched,
            "timestamp": user.last_enrichment_at,
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


@app.get("/api/dashboard/last-file")
def download_last_file(authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    authorize.jwt_required()
    email = authorize.get_jwt_subject()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.last_file_name:
        raise HTTPException(status_code=404, detail="No enrichment file available")
    companies = (
        db.query(CompanyUpdated)
        .filter(CompanyUpdated.uploaded_by == user.id)
        .filter(CompanyUpdated.source_file_name == user.last_file_name)
        .all()
    )
    if not companies:
        raise HTTPException(status_code=404, detail="No enrichment data found")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["name", "domain", "hq", "size", "employee_range", "industry", "linkedin_url"]
    )
    for c in companies:
        writer.writerow(
            [c.name, c.domain, c.hq, c.size, c.employee_range, c.industry, c.linkedin_url]
        )
    output.seek(0)
    headers = {"Content-Disposition": f"attachment; filename={user.last_file_name}"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)

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
        "employee_range",
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
    total_rows = 0

    for idx, row in enumerate(reader, start=1):
        total_rows += 1
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
            raw_size = clean(get("size"))
            size_int, size_range = parse_employee_size(raw_size)
            data_fields = {
                "name": clean(get("name")),
                "countries": countries or None,
                "hq": clean(get("hq")),
                "industry": clean(get("industry")),
                "subindustry": clean(get("subindustry")),
                "keywords_cntxt": keywords or None,
                "size": size_int,
                "employee_range": size_range,
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
        user.last_enrichment_at = datetime.now(timezone.utc)
        user.last_file_name = file.filename
        user.last_accounts_pushed = total_rows
        user.last_accounts_enriched = created + updated
        log_activity(user, "admin_upload")
        db.commit()

    return {"created": created, "updated": updated, "errors": errors}
