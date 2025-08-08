from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    enrichment_count = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime, nullable=True)
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
    size = Column(String)
    linkedin_url = Column(String)
