from sqlalchemy import text
from fastapi.testclient import TestClient

from test_auth import setup_app
from test_admin_upload import _create_company_table


def test_company_updated_pagination(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        for i in range(25):
            conn.execute(
                text("INSERT INTO company_updated (name, domain) VALUES (:n, :d)"),
                {"n": f"Company{i:02}", "d": f"example{i:02}.com"},
            )
    client = TestClient(app)
    resp = client.get(
        "/api/company_updated",
        params={"page": 2, "page_size": 10, "sort_key": "domain"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 25
    assert len(data["companies"]) == 10
    assert data["companies"][0]["domain"] == "example10.com"
