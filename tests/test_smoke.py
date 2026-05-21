from fastapi.testclient import TestClient

from app.main import create_app


def test_index_renders() -> None:
    with TestClient(create_app(seed_defaults=False)) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Task Solver" in response.text