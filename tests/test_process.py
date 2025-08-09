from fastapi.testclient import TestClient
from sqlalchemy import text

from test_auth import setup_app


def test_process_skips_rows_missing_identifiers(tmp_path):
    app, database, _ = setup_app(tmp_path)
    with database.engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_updated (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR,
                    domain VARCHAR UNIQUE,
                    countries VARCHAR,
                    hq VARCHAR,
                    industry VARCHAR,
                    subindustry VARCHAR,
                    keywords_cntxt VARCHAR,
                    size VARCHAR,
                    linkedin_url VARCHAR
                )
                """
            )
        )

    client = TestClient(app)

    resp = client.post(
        "/api/auth/signup",
        json={"email": "process_user@example.com", "password": "secret", "fullName": "Test"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    data = [
        {"Domain": "example.com", "Company Name": "Example Co"},
        {"Domain": "", "Company Name": "", "LinkedIn URL": ""},
    ]

    resp = client.post("/api/process", json={"data": data}, headers=headers)
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    resp = client.get("/api/results", params={"task_id": task_id})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["originalData"]["Domain"] == "example.com"


def test_process_requires_token(tmp_path):
    app, database, models = setup_app(tmp_path)
    client = TestClient(app)

    resp = client.post(
        "/api/auth/signup",
        json={"email": "auth@example.com", "password": "secret", "fullName": "Auth"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    db = database.SessionLocal()
    user = db.query(models.User).filter_by(email="auth@example.com").first()
    assert user.enrichment_count == 0

    resp = client.post("/api/process", json={"data": []})
    assert resp.status_code == 401
    db.refresh(user)
    assert user.enrichment_count == 0

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/process", json={"data": []}, headers=headers)
    assert resp.status_code == 200
    db.refresh(user)
    assert user.enrichment_count == 1
    db.close()

