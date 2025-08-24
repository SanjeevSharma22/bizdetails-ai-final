import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext

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

            if "username" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR"))
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
            if "last_enrichment_at" not in user_columns:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN last_enrichment_at TIMESTAMP")
                )
            if "activity_log" not in user_columns:
                if engine.dialect.name == "postgresql":
                    conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN activity_log JSON DEFAULT '[]'::json"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN activity_log JSON DEFAULT '[]'"
                        )
                    )
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

            if "slug" not in company_columns:
                conn.execute(
                    text("ALTER TABLE company_updated ADD COLUMN slug VARCHAR")
                )
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

    # Seed a default admin user if none exists
    from .models import User  # Import here to avoid circular dependency

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        admin_email = "admin"
        exists = db.query(User).filter(User.email == admin_email).first()
        if not exists:
            admin_user = User(
                email=admin_email,
                username="admin",
                hashed_password=pwd_context.hash("admin@123#"),
                full_name="Admin",
                role="Admin",
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
