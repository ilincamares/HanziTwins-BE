from datetime import datetime

import pytest

from services.user_service import UserService
from dtos.user_dtos import UserCreateRequest


class FakeUser:
    def __init__(self, user_id: int, username: str):
        self.id = user_id
        self.username = username
        self.created_at = datetime(2025, 1, 1, 12, 0, 0)


class FakeUserRepository:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def get_or_create(self, username: str):
        if username in self.users:
            return self.users[username]

        user = FakeUser(self.next_id, username)
        self.users[username] = user
        self.next_id += 1
        return user

    def get_by_id(self, user_id: int):
        for user in self.users.values():
            if user.id == user_id:
                return user

        return None

    def get_all(self):
        return list(self.users.values())


def test_create_or_load_user_creates_user():
    repository = FakeUserRepository()
    service = UserService(repository)

    result = service.create_or_load_user(
        UserCreateRequest(username="andrei")
    )

    assert result["id"] == 1
    assert result["username"] == "andrei"
    assert result["created_at"] == "2025-01-01T12:00:00"


def test_create_or_load_user_trims_username():
    repository = FakeUserRepository()
    service = UserService(repository)

    result = service.create_or_load_user(
        UserCreateRequest(username="  andrei  ")
    )

    assert result["username"] == "andrei"


def test_create_or_load_user_rejects_blank_username():
    repository = FakeUserRepository()
    service = UserService(repository)

    with pytest.raises(ValueError, match="Username cannot be empty"):
        service.create_or_load_user(
            UserCreateRequest(username="   ")
        )


def test_get_user_returns_existing_user():
    repository = FakeUserRepository()
    service = UserService(repository)

    created = service.create_or_load_user(
        UserCreateRequest(username="andrei")
    )

    result = service.get_user(created["id"])

    assert result["id"] == created["id"]
    assert result["username"] == "andrei"


def test_get_user_raises_lookup_error_if_missing():
    repository = FakeUserRepository()
    service = UserService(repository)

    with pytest.raises(LookupError, match="User not found"):
        service.get_user(999)


def test_get_users_returns_all_users():
    repository = FakeUserRepository()
    service = UserService(repository)

    service.create_or_load_user(UserCreateRequest(username="andrei"))
    service.create_or_load_user(UserCreateRequest(username="maria"))

    result = service.get_users()

    usernames = [user["username"] for user in result["users"]]

    assert usernames == ["andrei", "maria"]