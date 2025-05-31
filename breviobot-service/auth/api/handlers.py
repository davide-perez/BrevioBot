from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity, get_jwt, create_access_token, create_refresh_token
from dataclasses import dataclass
from core.logger import logger
from core.exceptions import ValidationError, AuthenticationError
from auth.authenticators import _jwt_auth_service
from sqlalchemy.exc import IntegrityError
from core.email_utils import send_email
from core.models.users import User
from persistence.repositories import UserRepository
from persistence.db_session import SessionLocal
import secrets
from core.settings import settings
from datetime import timedelta

@dataclass
class LoginRequest:
    username: str
    password: str
    
    @classmethod
    def from_json(cls, data: dict) -> 'LoginRequest':
        if not data.get("username"):
            raise ValidationError("Username is required")
        if not data.get("password"):
            raise ValidationError("Password is required")
        
        return cls(
            username=data["username"].strip(),
            password=data["password"]
        )

def handle_login_request(request_json):
    request_data = LoginRequest.from_json(request_json or {})
    auth_service = _jwt_auth_service
    user_db = auth_service.authenticate_user(request_data.username, request_data.password)
    if not settings.auth.refresh_token_expiry_minutes or settings.auth.refresh_token_expiry_minutes <= 0:
        raise ValidationError("Refresh token expiry (settings.auth.refresh_token_expiry_minutes) must be set to a positive integer.")
    access_token = auth_service.generate_token(user_db)
    refresh_token = create_refresh_token(
        identity=str(user_db.id),
        expires_delta=timedelta(minutes=settings.auth.refresh_token_expiry_minutes)
    )
    user_dict = User.model_validate(user_db).to_dict()
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.auth.token_expiry_minutes * 60,
        "refresh_expires_in": settings.auth.refresh_token_expiry_minutes * 60,
        "user": user_dict
    })


def handle_refresh_token_request(request_json):
    user_id = get_jwt_identity()
    with SessionLocal() as db:
        repo = UserRepository(db)
        user_db = repo.get(id=user_id)
        _jwt_auth_service.validate_user_status(user_db, require_verified=True)
    new_token = _jwt_auth_service.generate_token(user_db)
    return jsonify({
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": settings.auth.token_expiry_minutes * 60
    })

def handle_logout_request():
    logger.info("User logout")
    return jsonify({"message": "Successfully logged out"})

def handle_verify_user_request(token):
    if not token:
        raise AuthenticationError("Verification token is required")
    with SessionLocal() as db:
        repo = UserRepository(db)
        user = repo.get(verification_token=token)
        if not user:
            raise AuthenticationError("Invalid or expired verification token")
        repo.verify_user(user)
    return jsonify({"message": "Email verified successfully. You can now log in."})

def handle_create_user_request(user_data):
    if not user_data.get("username") or not user_data.get("email"):
        raise ValidationError("Username and email are required fields")
    if not user_data.get("password"):
        raise ValidationError("Password is required")
    with SessionLocal() as db:
        repo = UserRepository(db)
        existing_user = repo.get(username=user_data["username"])
        if existing_user:
            raise ValidationError(f"User with username '{user_data['username']}' already exists")
        verification_token = secrets.token_urlsafe(32)
        user = User(
            id=0,
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            is_active=True,
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
            user_dict = User.model_validate(db_user).to_dict()
            return jsonify({
                "username": user_dict["username"],
                "email": user_dict["email"],
                "message": "Registration successful. Please check your email to verify your account."
            })
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