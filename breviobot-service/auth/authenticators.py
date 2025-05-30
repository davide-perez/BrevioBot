from typing import Dict
from functools import wraps
from flask import g
from core.exceptions import ValidationError
from core.logger import logger
from core.exceptions import AuthenticationError
from persistence.repositories import UserRepository
from persistence.db_session import SessionLocal
from core.settings import settings
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request

ANONYMOUS_USER = {"role": "anonymous", "username": "anonymous"}

class JWTAuthService:
    def __init__(self) -> None:
        self.secret_key = settings.auth.secret_key
        if not self.secret_key:
            raise Exception("BREVIOBOT_JWT_SECRET_KEY environment variable must be set")
        self.token_expiry_hours = settings.auth.token_expiry_hours
        self.enable_auth = settings.auth.enable_auth

    def generate_token(self, user_db) -> str:
        user_id = getattr(user_db, 'id', None)
        if not user_id:
            raise ValidationError("User ID is required to generate a token")
        additional_claims = {
            'user_id': user_db.id,
            'username': user_db.username,
            'role': UserRepository.get_role(user_db)
        }
        return create_access_token(identity=str(user_db.id), additional_claims=additional_claims)
    
    def authenticate_user(self, username: str, password: str):
        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            user_db = repo.authenticate(username, password)
            if not user_db:
                logger.warning(f"Login attempt with invalid credentials: {username}")
                raise AuthenticationError("Invalid credentials")
            logger.info(f"Successful login for user: {username}")
            return user_db


def require_auth(f: callable) -> callable:
    @wraps(f)
    @jwt_required()
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_service = JWTAuthService()
        if not auth_service.enable_auth:
            g.current_user = ANONYMOUS_USER
            return f(*args, **kwargs)
        user_id = get_jwt_identity()
        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            user_db = repo.get_by_id(user_id)
            if not user_db or not getattr(user_db, "is_active", True):
                logger.warning(f"User not found or inactive: {user_id}")
                raise AuthenticationError("User not found or inactive")
            g.current_user = {
                "user_id": user_db.id,
                "username": user_db.username,
                "role": UserRepository.get_role(user_db)
            }
        return f(*args, **kwargs)
    return decorated_function


def optional_auth(f: callable) -> callable:
    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_service = JWTAuthService()
        if not auth_service.enable_auth:
            g.current_user = ANONYMOUS_USER
            return f(*args, **kwargs)
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
            if user_id:
                with SessionLocal() as db:
                    repo = UserRepository(lambda: db)
                    user_db = repo.get_by_id(user_id)
                    if user_db and getattr(user_db, "is_active", True):
                        g.current_user = {
                            "user_id": user_db.id,
                            "username": user_db.username,
                            "role": UserRepository.get_role(user_db)
                        }
                    else:
                        g.current_user = ANONYMOUS_USER
            else:
                g.current_user = ANONYMOUS_USER
        except Exception:
            g.current_user = ANONYMOUS_USER
        return f(*args, **kwargs)
    return decorated_function
