import traceback

from fastapi import APIRouter, HTTPException, Depends

from dtos.user_dtos import UserCreateRequest
from services.dependencies import get_user_service
from services.user_service import UserService

router = APIRouter()


@router.post("/")
def create_or_load_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.create_or_load_user(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}")
def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.get_user(user_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_users(
    user_service: UserService = Depends(get_user_service),
):
    try:
        return user_service.get_users()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))