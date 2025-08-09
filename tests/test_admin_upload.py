from fastapi.testclient import TestClient
from sqlalchemy import text

from test_auth import setup_app


def _create_company_table(engine):
    with engine.begin() as conn:
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
                    linkedin_url VARCHAR,
                    slug VARCHAR,
                    original_name VARCHAR,
                    legal_name VARCHAR
                )
                """
            )
        )


def _fetch_company(engine, domain):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT name, hq, size FROM company_updated WHERE domain=:d"),
            {"d": domain},
        ).mappings().first()
    return row


def _signup_admin(client):
    payload = {
        "email": "admin@example.com",
        "password": "secret",
        "fullName": "Admin",
        "role": "Admin",
    }
    resp = client.post("/api/auth/signup", json=payload)
    if resp.status_code != 200:
        resp = client.post("/api/auth/signin", json={"email": payload["email"], "password": payload["password"]})
        assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_override_mode_updates_and_preserves(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        conn.execute(
            text(
                "INSERT INTO company_updated (name, domain, hq, size) VALUES (:n, :d, :hq, :s)"
            ),
            {"n": "OldCo", "d": "example.com", "hq": "OldHQ", "s": "50"},
        )
    client = TestClient(app)
    headers = _signup_admin(client)

    csv_content = (
        "name,domain,countries,hq,industry,subindustry,keywords_cntxt,size,linkedin_url,slug,original_name,legal_name\n"
        "NewCo,example.com,, ,,, ,100,,,,\n"
    )
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {"mode": "override"}
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200
    row = _fetch_company(database.engine, "example.com")
    assert row["name"] == "NewCo"
    assert row["hq"] == "OldHQ"  # empty CSV should preserve existing
    assert row["size"] == "100"


def test_missing_mode_only_fills_empty(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        conn.execute(
            text(
                "INSERT INTO company_updated (name, domain, hq, size) VALUES (:n, :d, :hq, :s)"
            ),
            {"n": "OldCo", "d": "example.com", "hq": None, "s": "50"},
        )
    client = TestClient(app)
    headers = _signup_admin(client)

    csv_content = (
        "name,domain,countries,hq,industry,subindustry,keywords_cntxt,size,linkedin_url,slug,original_name,legal_name\n"
        "NewCo,example.com,,NewHQ,,, ,100,,,,\n"
    )
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {"mode": "missing"}
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200
    row = _fetch_company(database.engine, "example.com")
    assert row["name"] == "OldCo"  # existing name preserved
    assert row["hq"] == "NewHQ"  # hq was empty -> filled
    assert row["size"] == "50"  # existing value kept despite CSV


def test_upload_with_missing_optional_columns(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
    client = TestClient(app)
    headers = _signup_admin(client)

    csv_content = "domain\nexample.com\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {"mode": "override"}
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200
    row = _fetch_company(database.engine, "example.com")
    assert row["name"] is None


def test_column_mapping_allows_custom_headers(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
    client = TestClient(app)
    headers = _signup_admin(client)

    csv_content = "Company,Website\nAcme Corp,acme.com\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {
        "mode": "override",
        "column_map": '{"name":"Company","domain":"Website"}',
    }
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200
    row = _fetch_company(database.engine, "acme.com")
    assert row["name"] == "Acme Corp"
