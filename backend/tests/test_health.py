from fastapi.testclient import TestClient

from app.config import PHASE, SERVICE_NAME
from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_payload() -> None:
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["service"] == SERVICE_NAME
    assert data["phase"] == PHASE
