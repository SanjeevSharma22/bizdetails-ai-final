from fastapi.testclient import TestClient
from sqlalchemy import text
from test_auth import setup_app
from test_admin_upload import _create_company_table


def test_get_company_uses_db_when_present(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(
            text("INSERT INTO company_updated (name, domain) VALUES ('Existing', 'exist.com')")
        )

    def fail_fetch(*, name=None, domain=None, linkedin_url=None):
        raise AssertionError("API should not be called")

    monkeypatch.setattr(main, "fetch_company_data", fail_fetch)

    client = TestClient(app)
    resp = client.get("/api/company", params={"domain": "exist.com"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Existing"


def test_get_company_falls_back_to_api(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    import backend.app.main as main
    _create_company_table(database.engine)

    def fake_fetch(*, name=None, domain=None, linkedin_url=None):
        return {
            "name": "Deep Co",
            "domain": domain or name or "",
            "hq": "HQ",
            "size": "10",
            "industry": "Tech",
            "linkedin_url": "https://linkedin.com/company/deepco",
        }

    monkeypatch.setattr(main, "fetch_company_data", fake_fetch)

    client = TestClient(app)
    resp = client.get("/api/company", params={"domain": "deepco.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["domain"] == "deepco.com"
    assert data["name"] == "Deep Co"

    with database.engine.begin() as conn:
        row = conn.execute(
            text("SELECT name FROM company_updated WHERE domain=:d"),
            {"d": "deepco.com"},
        ).mappings().first()
    assert row is not None and row["name"] == "Deep Co"
