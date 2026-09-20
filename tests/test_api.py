from fastapi.testclient import TestClient
from agentguard.main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "AgentGuard" in response.text


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_policies():
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    assert "roles" in response.json()
