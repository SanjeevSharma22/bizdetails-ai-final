from fastapi.testclient import TestClient
from sqlalchemy import text
from test_auth import setup_app
from test_admin_upload import _create_company_table


def test_requires_identifier(tmp_path):
    app, _, _ = setup_app(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/company")
    assert resp.status_code == 400


def test_get_company_uses_db_when_present(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(
            text("INSERT INTO company_updated (name, domain) VALUES ('Existing', 'exist.com')")
        )

    def fail_fetch(*, name=None, domain=None, linkedin_url=None, **kwargs):
        raise AssertionError("API should not be called")

    monkeypatch.setattr(main, "fetch_company_data", fail_fetch)

    client = TestClient(app)
    resp = client.get("/api/company", params={"domain": "exist.com"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Existing"


def test_get_company_uses_slug_when_present(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO company_updated (name, domain, slug, linkedin_url) VALUES ('Existing', 'slug.com', 'slugco', 'https://linkedin.com/company/slugco')"
            )
        )

    def fail_fetch(*, name=None, domain=None, linkedin_url=None, **kwargs):
        raise AssertionError("API should not be called")

    monkeypatch.setattr(main, "fetch_company_data", fail_fetch)

    client = TestClient(app)
    resp = client.get(
        "/api/company",
        params={"linkedin_url": "https://linkedin.com/company/slugco"},
    )
    assert resp.status_code == 200
    assert resp.json()["domain"] == "slug.com"


def test_get_company_name_and_optional_fields(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO company_updated (name, domain, countries) VALUES ('Cisco', 'cisco.us', 'United States')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO company_updated (name, domain, countries) VALUES ('Cisco', 'cisco.ca', 'Canada')"
            )
        )

    def fail_fetch(*, name=None, domain=None, linkedin_url=None, **kwargs):
        raise AssertionError("API should not be called")

    monkeypatch.setattr(main, "fetch_company_data", fail_fetch)

    client = TestClient(app)
    resp = client.get(
        "/api/company", params={"name": "Cisco", "country": "Canada"}
    )
    assert resp.status_code == 200
    assert resp.json()["domain"] == "cisco.ca"


def test_get_company_falls_back_to_api(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)

    called = {}

    def fake_fetch(
        *,
        name=None,
        domain=None,
        linkedin_url=None,
        country=None,
        industry=None,
        subindustry=None,
        size=None,
        keywords=None,
    ):
        called.update(
            {
                "name": name,
                "domain": domain,
                "linkedin_url": linkedin_url,
                "country": country,
                "industry": industry,
                "subindustry": subindustry,
                "size": size,
                "keywords": keywords,
            }
        )
        return {
            "name": "Deep Co",
            "domain": domain or name or "",
            "hq": "HQ",
            "size": "10",
            "industry": "Tech",
            "linkedin_url": linkedin_url or "",
        }

    monkeypatch.setattr(main, "fetch_company_data", fake_fetch)

    client = TestClient(app)
    params = {
        "domain": "deepco.com",
        "name": "Deep Co",
        "linkedin_url": "https://linkedin.com/company/deepco",
        "country": "US",
        "industry": "Tech",
        "subindustry": "AI",
        "size": "100",
        "keywords": "cloud, ai",
    }
    resp = client.get("/api/company", params=params)
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "deepco.com"
    assert data["name"] == "Deep Co"
    assert called == {
        "name": "Deep Co",
        "domain": "deepco.com",
        "linkedin_url": "https://linkedin.com/company/deepco",
        "country": "US",
        "industry": "Tech",
        "subindustry": "AI",
        "size": "100",
        "keywords": ["cloud", "ai"],
    }

    with database.engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT name, linkedin_url FROM company_updated WHERE domain=:d"
            ),
            {"d": "deepco.com"},
        ).mappings().first()
    assert row is not None and row["name"] == "Deep Co"
    assert row["linkedin_url"] == "https://linkedin.com/company/deepco"
