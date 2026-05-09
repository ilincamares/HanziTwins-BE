from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from repositories import UserRepository, QuizAttemptRepository, ProgressRepository
from dtos.progress_dtos import QuizAttemptCreateRequest


router = APIRouter()


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