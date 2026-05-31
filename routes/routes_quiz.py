import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from services.quiz_service import QuizService
from services.dependencies import get_quiz_service

router = APIRouter()


@router.get("/generate")
def generate_quiz(
    hsk_level: str = Query("all", description="HSK level (1-6) or 'all'"),
    count: int = Query(5, description="Number of questions to generate."),
    difficulty: str = Query("medium", description="Difficulty: easy, medium, hard"),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    try:
        return quiz_service.generate_quiz(hsk_level, count, difficulty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))