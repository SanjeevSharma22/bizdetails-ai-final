import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1]))


def setup_app(tmp_path):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR NOT NULL UNIQUE, hashed_password VARCHAR NOT NULL)"
            )
        )

    os.environ["DATABASE_URL"] = db_url

    database = importlib.import_module("backend.app.database")
    models = importlib.import_module("backend.app.models")

    def create_only_users(bind=None, **kwargs):
        models.User.__table__.create(bind=bind or database.engine, checkfirst=True)

    database.Base.metadata.create_all = create_only_users

    main = importlib.import_module("backend.app.main")

    return main.app, database, models


def test_signup_and_tracking(tmp_path):
    app, database, models = setup_app(tmp_path)
    client = TestClient(app)

    # Sign up a new user
    resp = client.post(
        "/api/auth/signup",
        json={
            "email": "user@example.com",
            "password": "secret",
            "username": "testuser",
            "fullName": "Test User",
            "role": "Sales",
        },
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    db = database.SessionLocal()
    user = db.query(models.User).filter_by(email="user@example.com").first()
    assert user.full_name == "Test User"
    assert user.username == "testuser"
    assert user.role == "Sales"
    assert user.enrichment_count == 0
    assert user.account_status == "Active"
    assert user.last_login is None
    assert user.activity_log and user.activity_log[0]["action"] == "signup"

    # Sign in to update last_login
    resp = client.post(
        "/api/auth/signin",
        json={"email": "user@example.com", "password": "secret"},
    )
    assert resp.status_code == 200
    db.refresh(user)
    assert user.last_login is not None
    assert any(a["action"] == "signin" for a in user.activity_log)

    # Process a request to increment enrichment_count
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/process", json={"data": []}, headers=headers)
    assert resp.status_code == 200
    db.refresh(user)
    assert user.enrichment_count == 1
    assert user.last_enrichment_at is not None
    assert any(a["action"] == "enrichment" for a in user.activity_log)
    db.close()


def test_signup_accepts_name_field(tmp_path):
    app, database, models = setup_app(tmp_path)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/signup",
        json={
            "email": "user2@example.com",
            "password": "secret",
            "name": "Alt Name",
            "role": "Marketing",
        },
    )
    assert resp.status_code == 200

    db = database.SessionLocal()
    user = db.query(models.User).filter_by(email="user2@example.com").first()
    assert user.full_name == "Alt Name"
    db.close()


def test_signup_without_role_defaults(tmp_path):
    app, database, models = setup_app(tmp_path)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/signup",
        json={
            "email": "norole@example.com",
            "password": "secret",
            "fullName": "No Role",
        },
    )
    assert resp.status_code == 200

    db = database.SessionLocal()
    user = db.query(models.User).filter_by(email="norole@example.com").first()
    assert user.full_name == "No Role"
    assert user.role == "User"
    db.close()


def test_signup_without_fullname_defaults_to_email(tmp_path):
    app, database, models = setup_app(tmp_path)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/signup",
        json={
            "email": "noname@example.com",
            "password": "secret",
        },
    )
    assert resp.status_code == 200

    db = database.SessionLocal()
    user = db.query(models.User).filter_by(email="noname@example.com").first()
    assert user.full_name == "noname@example.com"
    assert user.username == "noname@example.com"
    assert user.role == "User"
    db.close()
