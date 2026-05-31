from datetime import datetime

import pytest

from services.progress_service import ProgressService
from dtos.progress_dtos import QuizAttemptCreateRequest


class FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class FakeAttempt:
    def __init__(self):
        self.id = 10
        self.user_id = 1
        self.hsk_level = "1"
        self.difficulty = "hard"
        self.score = 1
        self.total_questions = 2
        self.created_at = datetime(2025, 1, 1, 12, 0, 0)


class FakeUserRepository:
    def __init__(self, user_exists=True):
        self.user_exists = user_exists

    def get_by_id(self, user_id: int):
        if self.user_exists:
            return FakeUser(user_id)

        return None


class FakeQuizAttemptRepository:
    def __init__(self):
        self.created_attempt_payload = None

    def create_attempt(
        self,
        user_id,
        hsk_level,
        difficulty,
        score,
        total_questions,
        answers,
    ):
        self.created_attempt_payload = {
            "user_id": user_id,
            "hsk_level": hsk_level,
            "difficulty": difficulty,
            "score": score,
            "total_questions": total_questions,
            "answers": answers,
        }

        return FakeAttempt()

    def get_by_user_id(self, user_id: int):
        return []


class FakeProgressRepository:
    def __init__(self, missed_characters=None):
        self.missed_characters = missed_characters or []

    def get_progress_summary(self, user_id: int):
        return {
            "user_id": user_id,
            "total_quizzes": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy": 0.0,
            "most_missed_characters": [],
        }

    def get_most_missed_characters(self, user_id: int):
        return self.missed_characters


def make_service(
    user_exists=True,
    missed_characters=None,
):
    return ProgressService(
        user_repository=FakeUserRepository(user_exists=user_exists),
        quiz_attempt_repository=FakeQuizAttemptRepository(),
        progress_repository=FakeProgressRepository(
            missed_characters=missed_characters
        ),
    )


def test_save_quiz_attempt_success():
    service = make_service(user_exists=True)

    request = QuizAttemptCreateRequest(
        user_id=1,
        hsk_level="1",
        difficulty="hard",
        score=1,
        total_questions=2,
        answers=[
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
    )

    result = service.save_quiz_attempt(request)

    assert result["id"] == 10
    assert result["user_id"] == 1
    assert result["hsk_level"] == "1"
    assert result["difficulty"] == "hard"
    assert result["score"] == 1
    assert result["total_questions"] == 2


def test_save_quiz_attempt_user_not_found():
    service = make_service(user_exists=False)

    request = QuizAttemptCreateRequest(
        user_id=999,
        hsk_level="1",
        difficulty="hard",
        score=1,
        total_questions=1,
        answers=[],
    )

    with pytest.raises(LookupError, match="User not found"):
        service.save_quiz_attempt(request)


def test_save_quiz_attempt_rejects_score_greater_than_total():
    service = make_service(user_exists=True)

    request = QuizAttemptCreateRequest(
        user_id=1,
        hsk_level="1",
        difficulty="hard",
        score=3,
        total_questions=2,
        answers=[],
    )

    with pytest.raises(ValueError, match="Score cannot"):
        service.save_quiz_attempt(request)


def test_get_progress_summary_success():
    service = make_service(user_exists=True)

    result = service.get_progress_summary(user_id=1)

    assert result["user_id"] == 1
    assert result["total_quizzes"] == 0
    assert result["accuracy"] == 0.0


def test_get_progress_summary_user_not_found():
    service = make_service(user_exists=False)

    with pytest.raises(LookupError, match="User not found"):
        service.get_progress_summary(user_id=999)


def test_generate_review_quiz_without_mistakes_raises_error():
    service = make_service(user_exists=True, missed_characters=[])

    with pytest.raises(ValueError, match="No mistakes available"):
        service.generate_review_quiz(
            user_id=1,
            count=5,
            difficulty="medium",
        )