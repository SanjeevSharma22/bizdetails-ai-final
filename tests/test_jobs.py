from fastapi.testclient import TestClient
from sqlalchemy import text

from test_auth import setup_app
from test_admin_upload import _create_company_table
import json


def test_job_creation_and_metrics(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(
            text("INSERT INTO company_updated (name, domain) VALUES ('Existing', 'exist.com')")
        )

    def fake_fetch(*, name=None, domain=None, linkedin_url=None):
        return {
            "name": name or "AI Co",
            "domain": domain or "",
            "hq": "HQ",
            "size": "10",
            "industry": "Tech",
            "linkedin_url": "https://linkedin.com/company/aico",
            "countries": ["US"],
        }

    monkeypatch.setattr(main, "fetch_company_data", fake_fetch)

    client = TestClient(app)
    resp = client.post(
        "/api/auth/signup",
        json={"email": "job_user@example.com", "password": "secret", "fullName": "User"},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = "company_name,domain\nExisting,exist.com\nAI Company,aico.com\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    data = {"job_name": "job1", "strategy": "internal_then_ai_fallback"}
    resp = client.post("/api/jobs", headers=headers, data=data, files=files)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    resp = client.get("/api/jobs")
    assert resp.status_code == 200
    jobs = resp.json()["jobs"]
    job = next(j for j in jobs if j["job_id"] == job_id)
    assert job["progress"] == 100
    assert job["internal_pct"] > 0
    assert job["ai_pct"] > 0

    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    meta = resp.json()["meta"]
    assert meta["total_records"] == 2
    assert meta["processed_records"] == 2
    assert meta["internal_fields"] > 0
    assert meta["ai_fields"] > 0
    results = resp.json()["results"]
    assert len(results) == 2
    ai_row = next(r for r in results if r["domain"] == "aico.com")
    assert ai_row["sources"]["domain"] == "ai"


def test_job_creation_with_column_mapping(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)

    def fake_fetch(*, name=None, domain=None, linkedin_url=None):
        return {
            "name": name or "AI Co",
            "domain": domain or "",
            "hq": "HQ",
            "size": "10",
            "industry": "Tech",
            "linkedin_url": "https://linkedin.com/company/aico",
            "countries": ["US"],
        }

    monkeypatch.setattr(main, "fetch_company_data", fake_fetch)

    client = TestClient(app)
    resp = client.post(
        "/api/auth/signup",
        json={"email": "map_user@example.com", "password": "secret", "fullName": "User"},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = "CompanyName,WebDomain\nAI Company,aico.com\n"
    files = {"file": ("test.csv", csv_content, "text/csv")}
    column_map = json.dumps({"company_name": "companyname", "domain": "webdomain"})
    data = {
        "job_name": "jobmap",
        "strategy": "internal_then_ai_fallback",
        "column_map": column_map,
    }
    resp = client.post("/api/jobs", headers=headers, data=data, files=files)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    meta = resp.json()["meta"]
    assert meta["total_records"] == 1
