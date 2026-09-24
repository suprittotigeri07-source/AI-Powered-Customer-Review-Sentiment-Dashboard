from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def register(self, payload: RegisterRequest):
        if self.users.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = self.users.create(payload.email, hash_password(payload.password))
        token = create_access_token(str(user.id))
        return user, token

    def login(self, payload: LoginRequest):
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return user, create_access_token(str(user.id))
