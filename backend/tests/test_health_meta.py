def test_v1_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta_reports_sqlite_and_test_env(client):
    response = client.get("/api/v1/meta")
    assert response.status_code == 200
    assert response.json() == {"database": "sqlite", "app_env": "test"}
