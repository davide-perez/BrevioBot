import jwt
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from flask import request, jsonify, g

from core.settings import settings
from core.logger import logger
from .auth_exceptions import AuthenticationError, TokenExpiredError, InvalidTokenError, InvalidCredentialsError

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("BREVIOBOT_JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expiry_hours = int(os.getenv("BREVIOBOT_JWT_EXPIRY_HOURS", "24"))
        self.enable_auth = os.getenv("BREVIOBOT_ENABLE_AUTH", "true").lower() == "true"
    
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.hash_password(password) == hashed_password
    
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
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
    def get_token_from_request(self) -> Optional[str]:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        valid_users = {
            "admin": {
                "password_hash": self.hash_password("admin123"),
                "user_id": "1",
                "role": "admin"
            },
            "user": {
                "password_hash": self.hash_password("user123"),
                "user_id": "2", 
                "role": "user"
            }
        }
        
        if username not in valid_users:
            logger.warning(f"Login attempt with invalid username: {username}")
            raise InvalidCredentialsError("Invalid credentials")
        
        user_info = valid_users[username]
        if not self.verify_password(password, user_info["password_hash"]):
            logger.warning(f"Login attempt with invalid password for user: {username}")
            raise InvalidCredentialsError("Invalid credentials")
        
        return {
            "user_id": user_info["user_id"],
            "username": username,
            "role": user_info["role"]
        }

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        
        if not auth_service.enable_auth:
            g.current_user = {"username": "anonymous", "user_id": "anonymous"}
            return f(*args, **kwargs)
        
        try:
            token = auth_service.get_token_from_request()
            if not token:
                return jsonify({"error": "Authentication token required"}), 401
            
            payload = auth_service.verify_token(token)
            g.current_user = payload
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            return jsonify({"error": str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def optional_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_service = AuthService()
        
        try:
            token = auth_service.get_token_from_request()
            if token:
                payload = auth_service.verify_token(token)
                g.current_user = payload
            else:
                g.current_user = {"username": "anonymous", "user_id": "anonymous"}
        except AuthenticationError:
            g.current_user = {"username": "anonymous", "user_id": "anonymous"}
        
        return f(*args, **kwargs)
    return decorated_function
