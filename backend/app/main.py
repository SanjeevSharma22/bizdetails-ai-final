import os
import csv
import uuid
import re
from io import StringIO
from typing import Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

import pycountry

from .database import Base, engine, get_db
from .models import User, CompanyUpdated

# --- DB bootstrap ---
Base.metadata.create_all(bind=engine)

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
    confidence: str
    matchType: str
    notes: Optional[str]
    country: str
    industry: str

# In-memory task store (MVP)
TASK_RESULTS: Dict[str, List[ProcessedResult]] = {}

# --- Enrichment ---
def enrich_domains(
    data: List[Dict[str, Optional[str]]], db: Session
) -> List[ProcessedResult]:
    results: List[ProcessedResult] = []

    for idx, row in enumerate(data, start=1):
        domain = (row.get("Domain") or "").strip().lower()
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

        # 2) Fallback: company-name match with optional filters
        if not company:
            name = (row.get("Company Name") or "").strip().lower()
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
                    match_type = "Company Name" if not domain else "Domain+Company Name"
                else:
                    note = note or "Company not found"
            else:
                note = note or ("Domain not found" if domain else "Company not found")

        if company:
            result_country = (
                company.countries[0] if getattr(company, "countries", None) else ""
            )
            results.append(
                ProcessedResult(
                    id=idx,
                    companyName=company.name or "",
                    originalData=row,
                    domain=company.domain or domain,
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
                    companyName="",
                    originalData=row,
                    domain=domain,
                    confidence="Low",
                    matchType="None",
                    notes=note or "Not found",
                    country="",
                    industry="",
                )
            )
    return results

# --- Preprocessing helpers (optional) ---
LEGAL_SUFFIXES = {
    "inc", "inc.", "ltd", "ltd.", "pvt", "pvt.", "pvt ltd", "pvt. ltd",
    "llc", "corp", "co", "co.", "gmbh", "sa", "s.a.", "ag", "plc", "limited",
}

INDUSTRY_TAXONOMY = {
    "technology": "Technology",
    "tech": "Technology",
    "finance": "Finance",
    "financial services": "Finance",
    "healthcare": "Healthcare",
}

def strip_legal_suffixes(name: str) -> str:
    tokens = name.split()
    while tokens:
        token = re.sub(r"[^a-z.]", "", tokens[-1])
        if token in LEGAL_SUFFIXES:
            tokens.pop()
        else:
            break
    return " ".join(tokens)

def normalize_company_name(name: str) -> str:
    cleaned = name.strip().lower()
    cleaned = strip_legal_suffixes(cleaned)
    return cleaned

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

        identifier = (name, country, industry, subindustry, company_size, keywords)
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
    credentials: UserCredentials,
    db: Session = Depends(get_db),
    authorize: AuthJWT = Depends(),
):
    if db.query(User).filter(User.email == credentials.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(credentials.password)
    user = User(email=credentials.email, hashed_password=hashed_password)
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
async def process(req: ProcessRequest, db: Session = Depends(get_db)):
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

    # Require at least a domain OR company name per row
    for row in rows:
        has_domain = (row.get("Domain") or "").strip()
        has_name = (row.get("Company Name") or "").strip()
        if not (has_domain or has_name):
            raise HTTPException(
                status_code=400, detail="Domain or Company Name is required"
            )

    enriched = enrich_domains(rows, db)
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = enriched
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
