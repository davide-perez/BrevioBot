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

ANONYMOUS_USER = {"username": "anonymous"}

class JWTAuthService:
    def __init__(self) -> None:
        self.secret_key = settings.auth.secret_key
        if not self.secret_key:
            raise Exception("BREVIOBOT_JWT_SECRET_KEY environment variable must be set")
        self.token_expiry_hours = settings.auth.token_expiry_hours
        self.enable_auth = settings.auth.enable_auth

    def generate_token(self, user_db) -> str:
        user_id = None if not user_db else user_db.id
        if not user_id:
            raise ValidationError("User ID is required to generate a token")
        additional_claims = {
            'user_id': user_db.id,
            'username': user_db.username
        }
        return create_access_token(identity=str(user_db.id), additional_claims=additional_claims)
    
    def validate_user_status(self, user_db, require_verified=True):
        if not user_db:
            raise AuthenticationError("User not found")
        if not getattr(user_db, 'is_active', True):
            raise AuthenticationError("User not found or inactive")
        if require_verified and not getattr(user_db, 'is_verified', True):
            raise AuthenticationError("Email not verified. Please check your email for the verification link.")
        return True

    def authenticate_user(self, username: str, password: str):
        with SessionLocal() as db:
            repo = UserRepository(db)
            user_db = repo.authenticate(username, password)
            self.validate_user_status(user_db, require_verified=True)
            logger.info(f"Successful login for user: {username}")
            return user_db

_jwt_auth_service = JWTAuthService()

def require_auth(f: callable) -> callable:
    auth_service = _jwt_auth_service
    if not auth_service.enable_auth:
        @wraps(f)
        def decorated_function(*args: object, **kwargs: object) -> object:
            g.current_user = ANONYMOUS_USER
            return f(*args, **kwargs)
        return decorated_function
    else:
        @wraps(f)
        @jwt_required()
        def decorated_function(*args: object, **kwargs: object) -> object:
            user_id = get_jwt_identity()
            with SessionLocal() as db:
                repo = UserRepository(db)
                user_db = repo.get(id=user_id)
                try:
                    auth_service.validate_user_status(user_db, require_verified=True)
                    g.current_user = {
                        "user_id": user_db.id,
                        "username": user_db.username
                    }
                except AuthenticationError as e:
                    logger.warning(f"User not found or inactive: {user_id}")
                    g.current_user = ANONYMOUS_USER
                    raise
            return f(*args, **kwargs)
        return decorated_function
