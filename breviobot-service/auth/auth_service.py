import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from flask import request, jsonify, g

from core.settings import settings
from core.logger import logger
from core.exceptions import AuthenticationError
from persistence.user_repository import UserRepository
from persistence.db_session import SessionLocal
import bcrypt

class AuthService:
    def __init__(self) -> None:
        self.secret_key = os.getenv("BREVIOBOT_JWT_SECRET_KEY", "")
        if not self.secret_key:
            raise Exception("BREVIOBOT_JWT_SECRET_KEY environment variable must be set")
        self.algorithm = "HS256"
        self.token_expiry_hours = int(os.getenv("BREVIOBOT_JWT_EXPIRY_HOURS", "24"))
        self.enable_auth = os.getenv("BREVIOBOT_ENABLE_AUTH", "true").lower() == "true"

    def generate_token(self, user_data: Dict) -> str:
        payload = {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"Token verified for user_id: {payload.get('user_id')}, username: {payload.get('username')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            logger.warning("Token verification failed: Invalid token")
            raise AuthenticationError("Invalid token")
    def get_token_from_request(self) -> Optional[str]:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            user_db = repo.get_by_username(username)
            if not user_db:
                logger.warning(f"Login attempt with invalid username: {username}")
                raise AuthenticationError("Invalid credentials")

            if not bcrypt.checkpw(password.encode("utf-8"), user_db.password.encode("utf-8")):
                logger.warning(f"Login attempt with invalid password for user: {username}")
                raise AuthenticationError("Invalid credentials")

            logger.info(f"Successful login for user: {username}")
            user_info = {
                "user_id": user_db.id,
                "username": user_db.username,
                "email": user_db.email,
                "role": "admin" if getattr(user_db, "is_admin", False) else "user"
            }
            return user_info

def require_auth(f: callable) -> callable:
    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_service = AuthService()
        if not auth_service.enable_auth:
            g.current_user = {"role": "anonymous", "username": "anonymous"}
            return f(*args, **kwargs)
        token = auth_service.get_token_from_request()
        if not token:
            logger.warning("Authentication token is missing")
            raise AuthenticationError("Authentication token required")
        payload = auth_service.verify_token(token)
        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            user_db = repo.get_by_id(payload.get("user_id"))
            if not user_db or not getattr(user_db, "is_active", True):
                logger.warning(f"User not found or inactive: {payload.get('user_id')}")
                raise AuthenticationError("User not found or inactive")
            g.current_user = {
                "user_id": user_db.id,
                "username": user_db.username,
                "role": "admin" if getattr(user_db, "is_admin", False) else "user"
            }
        return f(*args, **kwargs)
    return decorated_function


def optional_auth(f: callable) -> callable:
    @wraps(f)
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_service = AuthService()
        token = auth_service.get_token_from_request()
        if token:
            payload = auth_service.verify_token(token)
            with SessionLocal() as db:
                repo = UserRepository(lambda: db)
                user_db = repo.get_by_id(payload.get("user_id"))
                if user_db and getattr(user_db, "is_active", True):
                    g.current_user = {
                        "user_id": user_db.id,
                        "username": user_db.username,
                        "role": "admin" if getattr(user_db, "is_admin", False) else "user"
                    }
                else:
                    g.current_user = {"role": "anonymous", "username": "anonymous"}
        else:
            g.current_user = {"role": "anonymous", "username": "anonymous"}
        return f(*args, **kwargs)
    return decorated_function
