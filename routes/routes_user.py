from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from repositories import UserRepository
from dtos.user_dtos import UserCreateRequest


router = APIRouter()


@router.post("/")
def create_or_load_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
):
    username = request.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    user_repository = UserRepository(db)
    user = user_repository.get_or_create(username)

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
):
    user_repository = UserRepository(db)
    users = user_repository.get_all()

    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]
    }