import pytest
from fastapi.testclient import TestClient

from main import app
from services.dependencies import get_quiz_service


class FakeQuizService:
    def __init__(self):
        self.received_args = None

    def generate_quiz(self, hsk_level: str, count: int, difficulty: str):
        self.received_args = {
            "hsk_level": hsk_level,
            "count": count,
            "difficulty": difficulty,
        }

        return {
            "metadata": {
                "hsk_level": hsk_level,
                "difficulty": difficulty,
                "questions_count": count,
            },
            "questions": [
                {
                    "target": "你",
                    "target_pinyin": "nǐ",
                    "options": [
                        {
                            "character": "你",
                            "pinyin": "nǐ",
                            "similarity": 100.0,
                            "is_correct": True,
                        },
                        {
                            "character": "他",
                            "pinyin": "tā",
                            "similarity": 95.0,
                            "is_correct": False,
                        },
                    ],
                }
            ],
        }


class ErrorQuizService:
    def __init__(self, error):
        self.error = error

    def generate_quiz(self, hsk_level: str, count: int, difficulty: str):
        raise self.error


@pytest.fixture()
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_generate_quiz_api_returns_quiz(client):
    service = FakeQuizService()
    app.dependency_overrides[get_quiz_service] = lambda: service

    response = client.get("/api/quiz/generate?hsk_level=2&count=3&difficulty=hard")

    assert response.status_code == 200

    data = response.json()

    assert data["metadata"]["hsk_level"] == "2"
    assert data["metadata"]["difficulty"] == "hard"
    assert data["metadata"]["questions_count"] == 3
    assert "questions" in data

    assert service.received_args == {
        "hsk_level": "2",
        "count": 3,
        "difficulty": "hard",
    }


def test_generate_quiz_api_uses_default_parameters(client):
    service = FakeQuizService()
    app.dependency_overrides[get_quiz_service] = lambda: service

    response = client.get("/api/quiz/generate")

    assert response.status_code == 200

    assert service.received_args == {
        "hsk_level": "all",
        "count": 5,
        "difficulty": "medium",
    }


def test_generate_quiz_api_rejects_invalid_count_type(client):
    service = FakeQuizService()
    app.dependency_overrides[get_quiz_service] = lambda: service

    response = client.get("/api/quiz/generate?count=abc")

    assert response.status_code == 422


def test_generate_quiz_api_converts_value_error_to_400(client):
    app.dependency_overrides[get_quiz_service] = lambda: ErrorQuizService(
        ValueError("Difficulty expert is not supported.")
    )

    response = client.get("/api/quiz/generate?difficulty=expert")

    assert response.status_code == 400
    assert response.json()["detail"] == "Difficulty expert is not supported."


def test_generate_quiz_api_converts_file_not_found_to_404(client):
    app.dependency_overrides[get_quiz_service] = lambda: ErrorQuizService(
        ValueError("HSK level must be between 1 and 6.")
    )

    response = client.get("/api/quiz/generate?hsk_level=9")

    assert response.status_code == 400
    assert response.json()["detail"] == "HSK level must be between 1 and 6."