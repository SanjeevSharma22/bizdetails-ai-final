from sqlalchemy import text
from fastapi.testclient import TestClient

from test_auth import setup_app
from test_admin_upload import _create_company_table


def test_company_result_limit_and_runtime_loading(tmp_path):
    app, database, _ = setup_app(tmp_path)
    _create_company_table(database.engine)
    with database.engine.begin() as conn:
        conn.execute(text("DELETE FROM company_updated"))
        for i in range(1105):
            conn.execute(
                text("INSERT INTO company_updated (name, domain) VALUES (:n, :d)"),
                {"n": f"Company{i:04}", "d": f"example{i:04}.com"},
            )
    client = TestClient(app)

    resp = client.get("/api/company_updated", params={"page": 1, "page_size": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1000
    assert len(data["companies"]) == 100
    assert data["companies"][0]["domain"] == "example0000.com"

    resp = client.get("/api/company_updated", params={"page": 11, "page_size": 100})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1105
    assert len(data["companies"]) == 100
    assert data["companies"][0]["domain"] == "example1000.com"
