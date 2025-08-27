from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    enrichment_count = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_enrichment_at = Column(DateTime(timezone=True), nullable=True)
    last_file_name = Column(String, nullable=True)
    last_accounts_pushed = Column(Integer, default=0, nullable=False)
    last_accounts_enriched = Column(Integer, default=0, nullable=False)
    activity_log = Column(JSON, default=list)
    account_status = Column(String, default="Active", nullable=False)


class CompanyUpdated(Base):
    __tablename__ = "company_updated"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    domain = Column(String, unique=True, index=True, nullable=False)
    countries = Column(ARRAY(String))
    hq = Column(String)
    industry = Column(String)
    subindustry = Column(String)
    keywords_cntxt = Column(ARRAY(String))
    size = Column(Integer)
    employee_range = Column(String)
    linkedin_url = Column(String)
    slug = Column(String)
    original_name = Column(String)
    legal_name = Column(String)
    uploaded_by = Column(Integer, nullable=True)
    source_file_name = Column(String, nullable=True)
