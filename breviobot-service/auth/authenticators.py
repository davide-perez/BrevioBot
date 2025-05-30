import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from flask import request, g
from core.exceptions import ValidationError
from core.logger import logger
from core.exceptions import AuthenticationError
from persistence.repositories import UserRepository
from persistence.db_session import SessionLocal
import bcrypt
from sqlalchemy.exc import IntegrityError
import secrets
from core.models.users import User
from core.email_utils import send_email
from core.settings import settings
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token, get_jwt

class JWTAuthService:
    def __init__(self) -> None:
        self.secret_key = settings.auth.secret_key
        if not self.secret_key:
            raise Exception("BREVIOBOT_JWT_SECRET_KEY environment variable must be set")
        self.algorithm = "HS256"
        self.token_expiry_hours = settings.auth.token_expiry_hours
        self.enable_auth = settings.auth.enable_auth

    def generate_token(self, user_data: Dict) -> str:
        user_id = user_data.get('user_id')
        if not user_id:
            raise ValidationError("User ID is required to generate a token")
        additional_claims = {
            'user_id': user_id,
            'username': user_data.get('username'),
            'role': user_data.get('role', 'user')
        }
        return create_access_token(identity=str(user_id), additional_claims=additional_claims)
    
    def verify_token(self, token: str) -> Dict:
        try:
            payload = decode_token(token, allow_expired=False, secret=self.secret_key, algorithms=[self.algorithm])
            logger.info(f"Token verified for user_id: {payload.get('sub')}, username: {payload.get('username')}")
            return payload
        except Exception as e:
            logger.warning(f"Token verification failed: {str(e)}")
            raise AuthenticationError("Invalid or expired token")
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
                "is_verified": user_db.is_verified,
                "role": "admin" if getattr(user_db, "is_admin", False) else "user"
            }
            return user_info

    @staticmethod
    def create_user(user_data: Dict) -> Dict:
        if not user_data.get("username") or not user_data.get("email"):
            raise ValidationError("Username and email are required fields")
        if not user_data.get("password"):
            raise ValidationError("Password is required")

        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            existing_user = repo.get_by_username(user_data["username"])
            if existing_user:
                raise ValidationError(f"User with username '{user_data['username']}' already exists")

            verification_token = secrets.token_urlsafe(32)

            user = User(
                id=0,
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data.get("full_name"),
                is_active=True,
                is_admin=user_data.get("is_admin", False),
                password=user_data["password"]
            )

            try:
                db_user = repo.create(user, is_verified=False, verification_token=verification_token)
                verify_url = f"http://localhost:8000/api/auth/verify?token={verification_token}"
                email_body = f"""
                    <p>Welcome to BrevioBot!</p>
                    <p>Please verify your email by clicking the link below:</p>
                    <p><a href='{verify_url}'>Verify Email</a></p>
                    <p>If you did not register, please ignore this email.</p>
                    """
                send_email(db_user.email, "Verify your email for BrevioBot", email_body)
                user_dict = User.model_validate(db_user).model_dump()
                return {
                    "username": user_dict["username"],
                    "email": user_dict["email"],
                    "role": "admin" if user_dict.get("is_admin") else "user",
                    "message": "Registration successful. Please check your email to verify your account."
                }
            except IntegrityError as e:
                db.rollback()
                import re
                msg = str(e.orig).lower()
                match = re.search(r'unique constraint failed: [\w]+\.([a-z_]+)', msg)
                if match:
                    field = match.group(1)
                    raise ValidationError(f"A user with this {field} already exists")
                else:
                    raise ValidationError("A user with the provided information already exists")

def require_auth(f: callable) -> callable:
    @wraps(f)
    @jwt_required()
    def decorated_function(*args: object, **kwargs: object) -> object:
        auth_service = JWTAuthService()
        if not auth_service.enable_auth:
            g.current_user = {"role": "anonymous", "username": "anonymous"}
            return f(*args, **kwargs)
        user_id = get_jwt_identity()
        claims = get_jwt()
        with SessionLocal() as db:
            repo = UserRepository(lambda: db)
            user_db = repo.get_by_id(user_id)
            if not user_db or not getattr(user_db, "is_active", True):
                logger.warning(f"User not found or inactive: {user_id}")
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
        auth_service = JWTAuthService()
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
