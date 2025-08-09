import os
import csv
import uuid
import re
from io import StringIO
from typing import Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from pydantic import BaseModel, Field, root_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

import pycountry

from .database import Base, engine, get_db, init_db
from .models import User, CompanyUpdated
from .normalization import normalize_company_name

# --- DB bootstrap ---
Base.metadata.create_all(bind=engine)
init_db()

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

# --- Schemas ---
class UserRole(str, Enum):
    SALES = "Sales"
    MARKETING = "Marketing"
    DATA_ANALYST = "Data Analyst"


class UserSignup(BaseModel):
    email: str
    password: str
    full_name: str = Field(..., alias="fullName")
    role: UserRole

    @root_validator(pre=True)
    def populate_fullname(cls, values):
        # Accept "name" as an alternative to "fullName" from clients
        if "fullName" not in values and "name" in values:
            values["fullName"] = values["name"]
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

# In-memory task store (MVP)
TASK_RESULTS: Dict[str, List[ProcessedResult]] = {}

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
    hashed_password = pwd_context.hash(credentials.password)
    user = User(
        email=credentials.email,
        hashed_password=hashed_password,
        full_name=credentials.full_name,
        role=credentials.role.value,
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

    # Require at least a domain OR company name OR LinkedIn URL per row
    for row in rows:
        has_domain = (row.get("Domain") or "").strip()
        has_name = (row.get("Company Name") or "").strip()
        has_linkedin = (row.get("LinkedIn URL") or "").strip()
        if not (has_domain or has_name or has_linkedin):
            raise HTTPException(
                status_code=400,
                detail="Domain, Company Name, or LinkedIn URL is required",
            )

    enriched = enrich_domains(rows, db)
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = enriched
    if user:
        user.enrichment_count += 1
        db.commit()
    return {"task_id": task_id}

@app.get("/api/results")
async def get_results(task_id: str):
    """Return processed results for a given task id."""
    return {"results": [r.dict() for r in TASK_RESULTS.get(task_id, [])]}

@app.get("/api/results/{task_id}/status")
async def task_status(task_id: str):
    status = "completed" if task_id in TASK_RESULTS else "pending"
    return {"task_id": task_id, "status": status}

@app.get("/api/dashboard")
async def dashboard():
    # TODO: wire real stats
    return {"stats": {}}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    return {"response": "Chat endpoint not implemented."}
