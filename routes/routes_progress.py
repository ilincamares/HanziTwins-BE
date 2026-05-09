from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from repositories import UserRepository, QuizAttemptRepository, ProgressRepository
from dtos.progress_dtos import QuizAttemptCreateRequest
import math
import random
import pandas
from fastapi import Query
from routes.routes_quiz import load_confusion_map, CHAR_TO_PINYIN



router = APIRouter()

def get_safe_pinyin(character: str) -> str:
    """
    Returns a JSON-safe pinyin value.

    If the pinyin is missing or invalid, the character itself is used
    as a fallback value.
    """
    value = CHAR_TO_PINYIN.get(character)

    if value is None:
        return character

    if pandas.isna(value):
        return character

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return character

    return value


def get_safe_similarity(score) -> float:
    """
    Returns a JSON-safe similarity value.
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(score):
        return 0.0

    return score


def get_difficulty_start_index(difficulty: str) -> int:
    """
    Determines which part of the nearest-neighbor list should be used
    based on the selected difficulty.
    """
    difficulty = difficulty.lower()

    if difficulty == "hard":
        return 0

    if difficulty == "medium":
        return 2

    return 4


def build_review_question(target: str, confusion_map: dict, difficulty: str) -> dict | None:
    """
    Builds one quiz question for a missed character.

    Returns None if the target character cannot be found in the confusion map.
    """
    if target not in confusion_map:
        return None

    neighbors_data = confusion_map.get(target, [])
    target_pinyin = get_safe_pinyin(target)

    options = [
        {
            "character": target,
            "pinyin": target_pinyin,
            "similarity": 100.0,
            "is_correct": True,
        }
    ]

    seen_pinyins = {target_pinyin}

    start_idx = get_difficulty_start_index(difficulty)
    distractors_found = 0

    for rh_char, score in neighbors_data[start_idx:]:
        rh_pinyin = get_safe_pinyin(rh_char)

        if rh_pinyin not in seen_pinyins:
            options.append(
                {
                    "character": rh_char,
                    "pinyin": rh_pinyin,
                    "similarity": get_safe_similarity(score),
                    "is_correct": False,
                }
            )

            seen_pinyins.add(rh_pinyin)
            distractors_found += 1

        if distractors_found == 3:
            break

    random.shuffle(options)

    return {
        "target": target,
        "target_pinyin": target_pinyin,
        "options": options,
    }


@router.get("/{user_id}/review")
def generate_review_quiz(
    user_id: int,
    count: int = Query(5, description="Number of review questions to generate."),
    difficulty: str = Query("medium", description="Difficulty: easy, medium, hard"),
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if count < 1:
        raise HTTPException(
            status_code=400,
            detail="Number of review questions must be greater than 0."
        )

    difficulty = difficulty.lower()

    if difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=400,
            detail=f"Difficulty {difficulty} is not supported."
        )

    progress_repository = ProgressRepository(db)
    missed_characters = progress_repository.get_most_missed_characters(user_id)

    if not missed_characters:
        raise HTTPException(
            status_code=404,
            detail="No mistakes available for review."
        )

    confusion_map = load_confusion_map("all")

    selected_mistakes = missed_characters[:count]

    questions = []

    for mistake in selected_mistakes:
        target = mistake["character"]

        question = build_review_question(
            target=target,
            confusion_map=confusion_map,
            difficulty=difficulty,
        )

        if question is not None:
            questions.append(question)

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No review questions could be generated from the recorded mistakes."
        )

    return {
        "metadata": {
            "mode": "review",
            "hsk_level": "personal",
            "difficulty": difficulty,
            "questions_count": len(questions),
        },
        "questions": questions,
    }

@router.post("/attempts")
def save_quiz_attempt(
    request: QuizAttemptCreateRequest,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(request.user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if request.score > request.total_questions:
        raise HTTPException(
            status_code=400,
            detail="Score cannot be greater than total questions."
        )

    quiz_attempt_repository = QuizAttemptRepository(db)

    answers_as_dicts = [
        answer.model_dump()
        for answer in request.answers
    ]

    attempt = quiz_attempt_repository.create_attempt(
        user_id=request.user_id,
        hsk_level=request.hsk_level,
        difficulty=request.difficulty,
        score=request.score,
        total_questions=request.total_questions,
        answers=answers_as_dicts,
    )

    return {
        "id": attempt.id,
        "user_id": attempt.user_id,
        "hsk_level": attempt.hsk_level,
        "difficulty": attempt.difficulty,
        "score": attempt.score,
        "total_questions": attempt.total_questions,
        "created_at": attempt.created_at.isoformat(),
    }


@router.get("/{user_id}")
def get_progress_summary(
    user_id: int,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    progress_repository = ProgressRepository(db)
    return progress_repository.get_progress_summary(user_id)


@router.get("/{user_id}/attempts")
def get_user_attempts(
    user_id: int,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    quiz_attempt_repository = QuizAttemptRepository(db)
    attempts = quiz_attempt_repository.get_by_user_id(user_id)

    return {
        "user_id": user_id,
        "attempts": [
            {
                "id": attempt.id,
                "hsk_level": attempt.hsk_level,
                "difficulty": attempt.difficulty,
                "score": attempt.score,
                "total_questions": attempt.total_questions,
                "created_at": attempt.created_at.isoformat(),
            }
            for attempt in attempts
        ],
    }


@router.get("/{user_id}/mistakes")
def get_user_mistakes(
    user_id: int,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    progress_repository = ProgressRepository(db)

    return {
        "user_id": user_id,
        "mistakes": progress_repository.get_most_missed_characters(user_id),
    }