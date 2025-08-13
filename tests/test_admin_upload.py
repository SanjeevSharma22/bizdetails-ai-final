from fastapi.testclient import TestClient
from sqlalchemy import text

from test_auth import setup_app


def _create_company_table(engine):
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS company_updated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        "username": "adminuser",
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


def test_upload_resets_autoincrement(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        # Insert a row with a manual ID to desync the autoincrement sequence
        conn.execute(
            text(
                "INSERT INTO company_updated (id, name, domain) VALUES (1, 'Existing', 'existing.com')"
            )
        )
        # Reset the sqlite sequence to force the next insert to reuse ID=1
        conn.execute(text("UPDATE sqlite_sequence SET seq=0 WHERE name='company_updated'"))

    client = TestClient(app)
    headers = _signup_admin(client)
    csv_content = "domain\nnew.com\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {"mode": "override"}
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200

    with database.engine.begin() as conn:
        rows = conn.execute(text("SELECT id, domain FROM company_updated ORDER BY id")).fetchall()
    assert [tuple(r) for r in rows] == [(1, "existing.com"), (2, "new.com")]


def test_upload_handles_header_whitespace(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
    client = TestClient(app)
    headers = _signup_admin(client)

    # Headers include extra spaces and mixed case
    csv_content = "CompanyName ,Website ,country\nAcme Corp,acme.com,US\n"
    files = {"file": ("data.csv", csv_content, "text/csv")}
    data = {
        "mode": "override",
        "column_map": '{"name":"CompanyName ","domain":"Website ","hq":"country"}',
    }
    resp = client.post(
        "/api/admin/company-updated/upload", headers=headers, files=files, data=data
    )
    assert resp.status_code == 200
    row = _fetch_company(database.engine, "acme.com")
    assert row["name"] == "Acme Corp"
    assert row["hq"] == "US"
