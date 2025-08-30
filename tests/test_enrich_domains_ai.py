from test_auth import setup_app
from test_admin_upload import _create_company_table
import importlib
from sqlalchemy import text


def test_enrich_domains_uses_ai_when_not_in_db(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    main = importlib.import_module("backend.app.main")
    _create_company_table(database.engine)

    called = {}

    def fake_fetch_batch(companies, batch_size=20):
        called["companies"] = companies
        return [
            {
                "name": "AI Corp",
                "domain": companies[0]["domain"],
                "hq": "AI HQ",
                "size": "1-10",
                "industry": "AI",
                "linkedin_url": companies[0]["linkedin_url"],
                "countries": ["US"],
            }
        ]

    monkeypatch.setattr(main, "fetch_companies_batch", fake_fetch_batch)

    db = database.SessionLocal()
    data = [
        {
            "Domain": "https://www.aiexample.com/",
            "Company Name": "AI Example",
            "LinkedIn URL": "https://linkedin.com/company/aiexample",
        }
    ]
    results, stats, internal_total, ai_total = main.process_job_rows(data, db)
    db.close()

    with database.engine.begin() as conn:
        row = conn.execute(
            text("SELECT name, domain FROM company_updated WHERE domain=:d"),
            {"d": "aiexample.com"},
        ).mappings().first()
    assert row is not None
    assert row["name"] == "AI Corp"

    assert called["companies"][0]["domain"] == "aiexample.com"
    assert called["companies"][0]["name"] == "AI Example"
    assert (
        called["companies"][0]["linkedin_url"]
        == "https://linkedin.com/company/aiexample"
    )

    assert len(results) == 1
    r = results[0]
    assert r.companyName == "AI Corp"
    assert r.domain == "aiexample.com"
    assert r.hq == "AI HQ"
    assert r.size is None
    assert r.employee_range == "1-10"
    assert r.linkedin_url == "https://linkedin.com/company/aiexample"
    assert r.country == "US"
    assert r.industry == "AI"
    assert r.matchType == "AI"
    assert r.confidence == "High"
    assert r.notes is None
    assert r.sources["companyName"] == "ai"
