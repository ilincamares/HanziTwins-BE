from repositories import UserRepository
from dtos.user_dtos import UserCreateRequest


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_or_load_user(
        self,
        request: UserCreateRequest,
    ):
        username = request.username.strip()

        if not username:
            raise ValueError("Username cannot be empty.")

        user = self.user_repository.get_or_create(username)

        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
        }


    def get_user(
        self,
        user_id: int,
    ):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
        }


    def get_users(
        self,
    ):
        users = self.user_repository.get_all()

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