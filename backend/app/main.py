import os
import csv
import uuid
import random
from io import StringIO
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User


Base.metadata.create_all(bind=engine)

app = FastAPI(title="BizDetails AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "secret")


@AuthJWT.load_config
def get_config():
    return Settings()


class UserCredentials(BaseModel):
    email: str
    password: str


class ProcessRequest(BaseModel):
    data: List[Dict[str, Optional[str]]]


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


TASK_RESULTS: Dict[str, List[ProcessedResult]] = {}


def generate_mock_domain(company_name: str) -> str:
    clean = "".join(ch for ch in company_name.lower() if ch.isalnum())
    domains = [".com", ".io", ".co", ".net"]
    return f"{clean}{random.choice(domains)}"


def generate_mock_results(data: List[Dict[str, Optional[str]]]) -> List[ProcessedResult]:
    results = []
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


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.reader(StringIO(text))
    headers = next(reader, [])
    return {"headers": headers}


@app.post("/api/process")
async def process(req: ProcessRequest):
    task_id = str(uuid.uuid4())
    TASK_RESULTS[task_id] = generate_mock_results(req.data)
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
