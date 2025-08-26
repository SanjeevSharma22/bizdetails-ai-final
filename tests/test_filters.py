from sqlalchemy import text
from fastapi.testclient import TestClient

from test_auth import setup_app
from test_admin_upload import _create_company_table


def _seed(db):
    with db.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        data = [
            {"n": "Google", "d": "google.com", "s": "10001+"},
            {"n": "Startup", "d": "startup.io", "s": "1-10"},
            {"n": "MidCorp", "d": "midcorp.net", "s": "201-500"},
        ]
        for row in data:
            conn.execute(
                text("INSERT INTO company_updated (name, domain, size) VALUES (:n, :d, :s)"),
                row,
            )


def test_domain_and_size_filters(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    _seed(database)
    client = TestClient(app)

    resp = client.get("/api/company_updated", params={"domain": "google.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["companies"][0]["domain"] == "google.com"

    resp = client.get(
        "/api/company_updated",
        params={"size_range": "1-10"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["companies"][0]["domain"] == "startup.io"
