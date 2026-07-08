from fastapi.testclient import TestClient

from app.main import create_app


def test_index_renders() -> None:
    with TestClient(create_app(seed_defaults=False)) as client:
        response = client.get("/")
        favicon = client.get("/static/favicon.svg")
        apple_touch_icon = client.get("/static/apple-touch-icon.png")

    assert response.status_code == 200
    assert "Task Solver" in response.text
    assert "Other domains" not in response.text
    assert 'id="add-task"' in response.text
    assert "View reports" not in response.text
    assert "Recently completed" in response.text
    assert 'rel="icon"' in response.text
    assert 'rel="apple-touch-icon"' in response.text
    assert '/static/favicon.svg' in response.text
    assert '/static/apple-touch-icon.png' in response.text
    assert 'data-theme-toggle' in response.text
    assert 'Dark theme' in response.text
    assert favicon.status_code == 200
    assert "<svg" in favicon.text
    assert apple_touch_icon.status_code == 200
    assert apple_touch_icon.headers["content-type"] == "image/png"
