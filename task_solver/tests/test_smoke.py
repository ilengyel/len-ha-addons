from fastapi.testclient import TestClient

from app.main import create_app


def test_index_renders() -> None:
    with TestClient(create_app(seed_defaults=False)) as client:
        response = client.get("/")
        favicon = client.get("/static/favicon.svg")

    assert response.status_code == 200
    assert "Task Solver" in response.text
    assert "Other domains" not in response.text
    assert 'id="add-task"' in response.text
    assert "View reports" not in response.text
    assert "Recently completed" in response.text
    assert 'rel="icon"' in response.text
    assert '/static/favicon.svg' in response.text
    assert favicon.status_code == 200
    assert "<svg" in favicon.text
