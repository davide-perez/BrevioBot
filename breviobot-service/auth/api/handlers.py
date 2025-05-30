from flask import jsonify, g
from dataclasses import dataclass
from core.logger import logger
from core.exceptions import ValidationError, AuthenticationError
from auth.authenticators import JWTAuthService
from sqlalchemy.exc import IntegrityError
from core.email_utils import send_email
from core.models.users import User
from persistence.repositories import UserRepository
from persistence.db_session import SessionLocal
import secrets

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

@dataclass
class RefreshTokenRequest:
    token: str
    
    @classmethod
    def from_json(cls, data: dict) -> 'RefreshTokenRequest':
        if not data.get("token"):
            raise ValidationError("Token is required")
        
        return cls(token=data["token"])

def handle_login_request(request_json):
    request_data = LoginRequest.from_json(request_json or {})
    auth_service = JWTAuthService()

    user_data = auth_service.authenticate_user(request_data.username, request_data.password)
    if not user_data.get("is_verified"):
        raise AuthenticationError("Email not verified. Please check your email for the verification link.")
    access_token = auth_service.generate_token(user_data)

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.token_expiry_hours * 3600,
        "user": {
            "username": user_data["username"],
            "email": user_data.get("email"),
            "role": user_data["role"]
        }
    })


def handle_refresh_token_request(request_json):
    request_data = RefreshTokenRequest.from_json(request_json or {})
    auth_service = JWTAuthService()
    payload = auth_service.verify_token(request_data.token)
    user_data = {
        "user_id": payload["user_id"],
        "username": payload["username"],
        "role": payload.get("role", "user")
    }
    new_token = auth_service.generate_token(user_data)
    logger.info(f"Token refreshed for user: {payload['username']}")
    return jsonify({
        "token": new_token,
        "expires_in": auth_service.token_expiry_hours * 3600
    })

def handle_logout_request():
    logger.info("User logout")
    return jsonify({"message": "Successfully logged out"})

def handle_me_request():
    if hasattr(g, 'current_user') and g.current_user:
        return jsonify({
            "user": {
                "username": g.current_user.get("username"),
                "user_id": g.current_user.get("user_id"),
                "role": g.current_user.get("role", "user")
            }
        })
    else:
        raise AuthenticationError("No authenticated user")

def handle_verify_user_request(token):
    if not token:
        raise AuthenticationError("Verification token is required")
    with SessionLocal() as db:
        repo = UserRepository(lambda: db)
        user = repo.get_by_field("verification_token", token)
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
            return jsonify({
                "username": user_dict["username"],
                "email": user_dict["email"],
                "role": "admin" if user_dict.get("is_admin") else "user",
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