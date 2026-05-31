from fastapi import Depends
from sqlalchemy.orm import Session

from database.connection import get_db

from repositories import (
    UserRepository,
    QuizAttemptRepository,
    ProgressRepository,
)

from services.user_service import UserService
from services.progress_service import ProgressService
from services.quiz_service import QuizService
from services.explorer_service import ExplorerService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    return UserService(user_repository)


def get_progress_service(db: Session = Depends(get_db)) -> ProgressService:
    user_repository = UserRepository(db)
    quiz_attempt_repository = QuizAttemptRepository(db)
    progress_repository = ProgressRepository(db)

    return ProgressService(
        user_repository=user_repository,
        quiz_attempt_repository=quiz_attempt_repository,
        progress_repository=progress_repository,
    )


def get_quiz_service() -> QuizService:
    return QuizService()


def get_explorer_service() -> ExplorerService:
    return ExplorerService()