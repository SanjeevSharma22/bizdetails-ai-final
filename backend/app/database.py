import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Ensure required columns exist in the database tables."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    with engine.begin() as conn:
        if "users" in table_names:
            user_columns = {col["name"] for col in inspector.get_columns("users")}

            if "full_name" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
            if "role" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR"))
            if "enrichment_count" not in user_columns:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN enrichment_count INTEGER NOT NULL DEFAULT 0"
                    )
                )
            if "last_login" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
            if "account_status" not in user_columns:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN account_status VARCHAR NOT NULL DEFAULT 'Active'"
                    )
                )

        if "company_updated" in table_names:
            company_columns = {
                col["name"] for col in inspector.get_columns("company_updated")
            }

            if "original_name" not in company_columns:
                conn.execute(
                    text(
                        "ALTER TABLE company_updated ADD COLUMN original_name VARCHAR"
                    )
                )
            if "legal_name" not in company_columns:
                conn.execute(
                    text(
                        "ALTER TABLE company_updated ADD COLUMN legal_name VARCHAR"
                    )
                )
