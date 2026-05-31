import pytest
from fastapi.testclient import TestClient

from main import app
from services.dependencies import get_explorer_service


class FakeExplorerService:
    def get_embedding_map(self, hsk_level: str, method: str):
        return {
            "metadata": {
                "hsk_level": hsk_level,
                "method": method,
                "count": 1,
            },
            "points": [
                {
                    "character": "你",
                    "pinyin": "nǐ",
                    "hsk_level": "1",
                    "x": 0.1,
                    "y": 0.2,
                    "cluster": 0,
                }
            ],
        }

    def get_character_neighbors(self, character: str, limit: int):
        return {
            "character": character,
            "pinyin": "nǐ",
            "neighbors": [
                {
                    "character": "他",
                    "pinyin": "tā",
                    "similarity": 95.0,
                }
            ],
        }


class ErrorExplorerService:
    def __init__(self, error):
        self.error = error

    def get_embedding_map(self, hsk_level: str, method: str):
        raise self.error

    def get_character_neighbors(self, character: str, limit: int):
        raise self.error


@pytest.fixture()
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_embedding_map_api_success(client):
    app.dependency_overrides[get_explorer_service] = lambda: FakeExplorerService()

    response = client.get("/api/explorer/map?hsk_level=1&method=umap")

    assert response.status_code == 200

    data = response.json()

    assert data["metadata"]["hsk_level"] == "1"
    assert data["metadata"]["method"] == "umap"
    assert len(data["points"]) == 1


def test_get_character_neighbors_api_success(client):
    app.dependency_overrides[get_explorer_service] = lambda: FakeExplorerService()

    response = client.get("/api/explorer/你/neighbors?limit=5")

    assert response.status_code == 200

    data = response.json()

    assert data["character"] == "你"
    assert data["neighbors"][0]["character"] == "他"


def test_get_embedding_map_api_value_error(client):
    app.dependency_overrides[get_explorer_service] = lambda: ErrorExplorerService(
        ValueError("Projection method must be either 'umap' or 'tsne'.")
    )

    response = client.get("/api/explorer/map?method=pca")

    assert response.status_code == 400
    assert "Projection method" in response.json()["detail"]


def test_get_character_neighbors_api_not_found(client):
    app.dependency_overrides[get_explorer_service] = lambda: ErrorExplorerService(
        LookupError("Character not found.")
    )

    response = client.get("/api/explorer/不存在/neighbors")

    assert response.status_code == 404
    assert response.json()["detail"] == "Character not found."