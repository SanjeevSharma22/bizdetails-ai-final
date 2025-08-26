from test_auth import setup_app
from test_admin_upload import _create_company_table
import importlib
from sqlalchemy import text


def test_enrich_domains_uses_ai_when_not_in_db(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    main = importlib.import_module("backend.app.main")
    _create_company_table(database.engine)

    called = {}

    def fake_fetch(*, name=None, domain=None, linkedin_url=None):
        called['args'] = {'name': name, 'domain': domain, 'linkedin_url': linkedin_url}
        return {
            "name": "AI Corp",
            "domain": domain,
            "hq": "AI HQ",
            "size": "1-10",
            "industry": "AI",
            "linkedin_url": linkedin_url,
            "countries": ["US"],
        }

    monkeypatch.setattr(main, "fetch_company_data", fake_fetch)

    db = database.SessionLocal()
    data = [{
        "Domain": "https://www.aiexample.com/",
        "Company Name": "AI Example",
        "LinkedIn URL": "https://linkedin.com/company/aiexample",
    }]
    results = main.enrich_domains(data, db)
    db.close()

    with database.engine.begin() as conn:
        row = conn.execute(
            text("SELECT name, domain FROM company_updated WHERE domain=:d"),
            {"d": "aiexample.com"},
        ).mappings().first()
    assert row is not None
    assert row["name"] == "AI Corp"

    assert called['args']['domain'] == "aiexample.com"
    assert called['args']['name'] == "AI Example"
    assert called['args']['linkedin_url'] == "https://linkedin.com/company/aiexample"

    assert len(results) == 1
    r = results[0]
    assert r.companyName == "AI Corp"
    assert r.domain == "aiexample.com"
    assert r.hq == "AI HQ"
    assert r.size == "1-10"
    assert r.linkedin_url == "https://linkedin.com/company/aiexample"
    assert r.country == "US"
    assert r.industry == "AI"
    assert r.matchType == "AI"
    assert r.confidence == "High"
    assert r.notes is None
    assert r.sources["companyName"] == "ai"
