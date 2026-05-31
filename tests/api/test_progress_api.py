import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database.connection import Base, get_db


@pytest.fixture()
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db):
    with TestClient(app) as test_client:
        yield test_client


def create_test_user(client, username="andrei"):
    response = client.post(
        "/api/users/",
        json={"username": username},
    )

    assert response.status_code == 200
    return response.json()


def valid_attempt_payload(user_id: int):
    return {
        "user_id": user_id,
        "hsk_level": "1",
        "difficulty": "hard",
        "score": 1,
        "total_questions": 2,
        "answers": [
            {
                "target_character": "你",
                "target_pinyin": "nǐ",
                "selected_character": "你",
                "selected_pinyin": "nǐ",
                "is_correct": True,
                "similarity": 100.0,
            },
            {
                "target_character": "好",
                "target_pinyin": "hǎo",
                "selected_character": "妈",
                "selected_pinyin": "mā",
                "is_correct": False,
                "similarity": 82.0,
            },
        ],
    }


def test_save_quiz_attempt(client):
    user = create_test_user(client)

    response = client.post(
        "/api/progress/attempts",
        json=valid_attempt_payload(user["id"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert data["user_id"] == user["id"]
    assert data["hsk_level"] == "1"
    assert data["difficulty"] == "hard"
    assert data["score"] == 1
    assert data["total_questions"] == 2
    assert "created_at" in data


def test_save_quiz_attempt_user_not_found(client):
    response = client.post(
        "/api/progress/attempts",
        json=valid_attempt_payload(999),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_save_quiz_attempt_rejects_score_greater_than_total(client):
    user = create_test_user(client)

    payload = valid_attempt_payload(user["id"])
    payload["score"] = 3
    payload["total_questions"] = 2

    response = client.post(
        "/api/progress/attempts",
        json=payload,
    )

    assert response.status_code == 400
    assert "Score cannot" in response.json()["detail"]


def test_save_quiz_attempt_rejects_negative_score(client):
    user = create_test_user(client)

    payload = valid_attempt_payload(user["id"])
    payload["score"] = -1

    response = client.post(
        "/api/progress/attempts",
        json=payload,
    )

    assert response.status_code == 422


def test_save_quiz_attempt_rejects_zero_total_questions(client):
    user = create_test_user(client)

    payload = valid_attempt_payload(user["id"])
    payload["score"] = 0
    payload["total_questions"] = 0
    payload["answers"] = []

    response = client.post(
        "/api/progress/attempts",
        json=payload,
    )

    assert response.status_code == 422


def test_get_empty_progress_summary(client):
    user = create_test_user(client)

    response = client.get(f"/api/progress/{user['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["total_quizzes"] == 0
    assert data["total_questions"] == 0
    assert data["correct_answers"] == 0
    assert data["accuracy"] == 0.0
    assert data["most_missed_characters"] == []


def test_get_progress_summary_after_attempt(client):
    user = create_test_user(client)

    save_response = client.post(
        "/api/progress/attempts",
        json=valid_attempt_payload(user["id"]),
    )

    assert save_response.status_code == 200

    response = client.get(f"/api/progress/{user['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["total_quizzes"] == 1
    assert data["total_questions"] == 2
    assert data["correct_answers"] == 1
    assert data["accuracy"] == 50.0

    assert len(data["most_missed_characters"]) == 1
    assert data["most_missed_characters"][0]["character"] == "好"
    assert data["most_missed_characters"][0]["target_pinyin"] == "hǎo"
    assert data["most_missed_characters"][0]["mistakes"] == 1


def test_get_progress_summary_user_not_found(client):
    response = client.get("/api/progress/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_get_user_attempts_empty(client):
    user = create_test_user(client)

    response = client.get(f"/api/progress/{user['id']}/attempts")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["attempts"] == []


def test_get_user_attempts_after_saving_attempt(client):
    user = create_test_user(client)

    save_response = client.post(
        "/api/progress/attempts",
        json=valid_attempt_payload(user["id"]),
    )

    assert save_response.status_code == 200

    response = client.get(f"/api/progress/{user['id']}/attempts")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert len(data["attempts"]) == 1

    attempt = data["attempts"][0]

    assert attempt["hsk_level"] == "1"
    assert attempt["difficulty"] == "hard"
    assert attempt["score"] == 1
    assert attempt["total_questions"] == 2
    assert "created_at" in attempt


def test_get_user_attempts_user_not_found(client):
    response = client.get("/api/progress/999/attempts")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_get_user_mistakes_empty(client):
    user = create_test_user(client)

    response = client.get(f"/api/progress/{user['id']}/mistakes")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["mistakes"] == []


def test_get_user_mistakes_after_wrong_answers(client):
    user = create_test_user(client)

    first_payload = valid_attempt_payload(user["id"])

    second_payload = {
        "user_id": user["id"],
        "hsk_level": "1",
        "difficulty": "medium",
        "score": 0,
        "total_questions": 1,
        "answers": [
            {
                "target_character": "好",
                "target_pinyin": "hǎo",
                "selected_character": "妈",
                "selected_pinyin": "mā",
                "is_correct": False,
                "similarity": 82.0,
            }
        ],
    }

    first_response = client.post(
        "/api/progress/attempts",
        json=first_payload,
    )

    second_response = client.post(
        "/api/progress/attempts",
        json=second_payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    response = client.get(f"/api/progress/{user['id']}/mistakes")

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user["id"]
    assert len(data["mistakes"]) == 1

    assert data["mistakes"][0]["character"] == "好"
    assert data["mistakes"][0]["target_pinyin"] == "hǎo"
    assert data["mistakes"][0]["mistakes"] == 2


def test_get_user_mistakes_user_not_found(client):
    response = client.get("/api/progress/999/mistakes")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_generate_review_quiz_user_not_found(client):
    response = client.get("/api/progress/999/review")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_generate_review_quiz_without_mistakes(client):
    user = create_test_user(client)

    response = client.get(f"/api/progress/{user['id']}/review")

    assert response.status_code == 400
    assert response.json()["detail"] == "No mistakes available for review."