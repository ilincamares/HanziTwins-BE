import traceback

from fastapi import APIRouter, HTTPException, Depends, Query

from dtos.progress_dtos import QuizAttemptCreateRequest
from services.progress_service import ProgressService
from services.dependencies import get_progress_service

router = APIRouter()


@router.get("/{user_id}/review")
def generate_review_quiz(
    user_id: int,
    count: int = Query(5, description="Number of review questions to generate."),
    difficulty: str = Query("medium", description="Difficulty: easy, medium, hard"),
    progress_service: ProgressService = Depends(get_progress_service),
):
    try:
        return progress_service.generate_review_quiz(user_id, count, difficulty)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attempts")
def save_quiz_attempt(
    request: QuizAttemptCreateRequest,
    progress_service: ProgressService = Depends(get_progress_service),
):
    try:
        return progress_service.save_quiz_attempt(request)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
def get_progress_summary(
    user_id: int,
    progress_service: ProgressService = Depends(get_progress_service),
):
    try:
        return progress_service.get_progress_summary(user_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/attempts")
def get_user_attempts(
    user_id: int,
    progress_service: ProgressService = Depends(get_progress_service),
):
    try:
        return progress_service.get_user_attempts(user_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/mistakes")
def get_user_mistakes(
    user_id: int,
    progress_service: ProgressService = Depends(get_progress_service),
):
    try:
        return progress_service.get_user_mistakes(user_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))