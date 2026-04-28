from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Ensure the engine is running and accepting connections."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Server is running"}

