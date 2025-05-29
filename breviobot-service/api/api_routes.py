from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from core.settings import settings
from core.exceptions import ValidationError, InvalidCredentialsError
from core.logger import logger
from .api_handlers import (
    handle_validation_error,
    handle_general_error,
    handle_summarize_request,
    handle_transcribe_request,
    handle_authentication_error,
    handle_create_user_request,
    handle_login_request
)
from auth.auth_handlers import (
    handle_refresh_token_request, 
    handle_logout_request, 
    handle_me_request
)
from core.exceptions import AuthenticationError
from auth.auth_service import require_auth

app = Flask(__name__)
CORS(app, origins=settings.api.cors_origins)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

# Error handlers
app.errorhandler(AuthenticationError)(handle_authentication_error)
app.errorhandler(InvalidCredentialsError)(handle_authentication_error)
app.errorhandler(ValidationError)(handle_validation_error)
app.errorhandler(Exception)(handle_general_error)

# Authentication routes
@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    return handle_login_request(request.get_json())

@app.route("/api/auth/refresh", methods=["POST"])
@limiter.limit("10 per minute")
def refresh_token():
    return handle_refresh_token_request(request.get_json())

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    return handle_logout_request()

@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    return handle_me_request()

# Service routes
@app.route("/api/summarize", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def summarize():
    return handle_summarize_request(request.json)

@app.route("/api/transcribe", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def transcribe():
    return handle_transcribe_request(request.files, request.form)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}, 200
    
@app.route("/api/users", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
def create_user():
    user_data = request.get_json()
    return handle_create_user_request(user_data)

@app.route("/api/users/verify", methods=["GET"])
def verify_user():
    token = request.args.get("token")
    from .api_handlers import handle_verify_user_request
    return handle_verify_user_request(token)

@app.route('/favicon.ico')
def favicon():
    return '', 204
