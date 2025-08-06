import os
import csv
import uuid
import random
import re
from io import StringIO

from typing import Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

import pycountry

from .database import Base, engine, get_db
from .models import User

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BizDetails AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "secret")

@AuthJWT.load_config
def get_config():
    return Settings()


# ---- Data models ----

class UserCredentials(BaseModel):
    email: str
    password: str

class ProcessRequest(BaseModel):
    data: List[Dict[str, Optional[str]]]
    mapping: Optional[Dict[str, str]] = None

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

# In‐memory store for demo
TASK_RESULTS: Dict[str, List[ProcessedResult]] = {}


def generate_mock_domain(company_name: str) -> str:
    clean = "".join(ch for ch in company_name.lower() if ch.isalnum())
    domains = [".com", ".io", ".co", ".net"]
    return f"{clean}{random.choice(domains)}"

def generate_mock_results(data: List[Dict[str, Optional[str]]]) -> List[ProcessedResult]:
    results: List[ProcessedResult] = []
    for idx, row in enumerate(data, start=1):
        name = row.get("Company Name") or f"Company {idx}"
        results.append(
            ProcessedResult(
                id=idx,
                companyName=name,
                originalData=row,
                domain=generate_mock_domain(name),
                confidence=random.choice(["High", "Medium", "Low"]),
                matchType=random.choice(["Exact", "Contextual", "Reverse", "Manual"]),
                notes=None,
                country=row.get("Country") or "US",
                industry=row.get("Industry") or "Technology",
            )
        )
    return results


# ---- Preprocessing utilities ----

LEGAL_SUFFIXES = {
    "inc",
    "inc.",
    "ltd",
    "ltd.",
    "pvt",
    "pvt.",
    "pvt ltd",
    "pvt. ltd",
    "llc",
    "corp",
    "co",
    "co.",
    "gmbh",
    "sa",
    "s.a.",
    "ag",
    "plc",
    "limited",
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
        return None
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

# ---- Auth endpoints ----

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


# ---- Upload & processing ----

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.reader(StringIO(text))
    headers = next(reader, [])
    return {"headers": headers}

@app.post("/api/process")
async def process(req: ProcessRequest):
    rows = req.data
    if req.mapping:
        mapped_rows: List[Dict[str, Optional[str]]] = []
        for row in rows:
            mapped_row = {}
            for field, col in req.mapping.items():
                mapped_row[field] = row.get(col)
            mapped_rows.append(mapped_row)
        rows = mapped_rows

    processed = preprocess_rows(rows)
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = generate_mock_results(processed)
    return {"task_id": task_id}

@app.get("/api/results")
async def get_results(task_id: str):
    return {"results": [r.dict() for r in TASK_RESULTS.get(task_id, [])]}

@app.get("/api/results/{task_id}/status")
async def task_status(task_id: str):
    status = "completed" if task_id in TASK_RESULTS else "pending"
    return {"task_id": task_id, "status": status}

@app.get("/api/dashboard")
async def dashboard():
    return {"stats": {}}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    return {"response": "Chat endpoint not implemented."}
