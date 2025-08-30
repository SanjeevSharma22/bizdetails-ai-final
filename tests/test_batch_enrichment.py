import importlib

from sqlalchemy import text

from test_auth import setup_app
from test_admin_upload import _create_company_table


def test_internal_before_external(tmp_path, monkeypatch):
    app, database, _ = setup_app(tmp_path)
    main = importlib.import_module("backend.app.main")
    _create_company_table(database.engine)

    # Seed one company so it is found internally
    with database.engine.begin() as conn:
        conn.execute(
            text("INSERT INTO company_updated (name, domain) VALUES ('Internal', 'inside.com')")
        )

    captured = {}

    def fake_batch(companies, batch_size=20):
        captured["companies"] = companies
        return [
            {
                "name": "External Corp",
                "domain": c["domain"],
                "hq": "HQ",
                "size": "1-10",
                "industry": "Tech",
                "linkedin_url": c.get("linkedin_url"),
                "countries": ["US"],
            }
            for c in companies
        ]

    monkeypatch.setattr(main, "fetch_companies_batch", fake_batch)

    db = database.SessionLocal()
    data = [
        {"Domain": "inside.com", "Company Name": "Internal"},
        {"Domain": "outside.com", "Company Name": "External"},
    ]
    results, stats, internal_total, ai_total = main.process_job_rows(data, db)
    db.close()

    # Only the unresolved company should be sent to DeepSeek
    assert len(captured["companies"]) == 1
    assert captured["companies"][0]["domain"] == "outside.com"

    # Results should preserve order and mark sources appropriately
    assert len(results) == 2
    assert results[0].domain == "inside.com" and results[0].matchType == "Internal"
    assert results[1].domain == "outside.com" and results[1].matchType == "AI"


def test_fetch_companies_batch_chunks_requests(monkeypatch):
    main = importlib.import_module("backend.app.deepseek")

    calls = []

    def fake_post(self, path, json=None, headers=None):
        calls.append(json)
        # Echo back simple payloads for each input
        return type(
            "Resp",
            (),
            {
                "status_code": 200,
                "json": lambda self: {
                    "data": [
                        {
                            "name": f"C{i}",
                            "domain": "d{i}.com".format(i=i),
                            "countries": ["US"],
                            "hq": None,
                            "industry": None,
                            "subindustries": [],
                            "keywords_cntxt": [],
                            "size": None,
                            "linkedin_url": None,
                            "slug": None,
                            "original_name": None,
                            "legal_name": None,
                        }
                        for i in range(len(json["input"]))
                    ]
                },
            },
        )()

    monkeypatch.setattr(main.httpx.Client, "post", fake_post, raising=False)
    monkeypatch.setattr(main, "_require_api_key", lambda: "test-key")

    companies = [{"name": f"C{i}", "domain": f"d{i}.com"} for i in range(5)]
    results = main.fetch_companies_batch(companies, batch_size=2)

    # Expect ceil(5/2) == 3 HTTP calls
    assert len(calls) == 3
    assert len(results) == 5
