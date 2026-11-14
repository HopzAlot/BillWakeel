
from fastapi.testclient import TestClient

from main import app
from config import settings

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_frontend():
    response = client.options(
        "/health",
        headers={
            "Origin": settings.frontend_origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        settings.frontend_origin
    )
