from typing import Any

from sqlalchemy.orm import Session

from database.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_username(self, username: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.username == username)
            .first()
        )

    def create(self, username: str) -> User:
        username = username.strip()

        user = User(username=username)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_or_create(self, username: str) -> User:
        username = username.strip()

        existing_user = self.get_by_username(username)

        if existing_user:
            return existing_user

        return self.create(username)

    def get_all(self) -> list[type[User]]:
        return (
            self.db.query(User)
            .order_by(User.username.asc())
            .all()
        )