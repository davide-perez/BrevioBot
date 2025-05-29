from flask import jsonify, g
from dataclasses import dataclass
from typing import Dict

from .auth_service import AuthService
from core.exceptions import AuthenticationError, InvalidCredentialsError
from core.exceptions import ValidationError
from core.logger import logger

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
    auth_service = AuthService()
    
    try:
        user_data = auth_service.authenticate_user(request_data.username, request_data.password)
        token = auth_service.generate_token(user_data)
        
        logger.info(f"Successful login for user: {request_data.username}")
        return jsonify({
            "token": token,
            "user": {
                "username": user_data["username"],
                "user_id": user_data["user_id"],
                "role": user_data.get("role", "user")
            },
            "expires_in": auth_service.token_expiry_hours * 3600  # seconds
        })
    
    except InvalidCredentialsError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

def handle_refresh_token_request(request_json):
    request_data = RefreshTokenRequest.from_json(request_json or {})
    auth_service = AuthService()
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
        return jsonify({"error": "No authenticated user"}), 401

def handle_authentication_error(error):
    logger.warning(f"Authentication error: {str(error)}")
    return jsonify({"error": str(error)}), 401
