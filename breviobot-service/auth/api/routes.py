from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import jwt_required, get_jwt_identity
from core.settings import settings
from auth.api.handlers import (
    handle_create_user_request,
    handle_login_request,
    handle_refresh_token_request, 
    handle_verify_user_request,
    handle_logout_request
)
from auth.authenticators import require_auth

auth_bp = Blueprint("auth_api", __name__)

auth_limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

@auth_bp.route("/api/auth/login", methods=["POST"])
@auth_limiter.limit("10 per minute")
def login():
    return handle_login_request(request.get_json())

@auth_bp.route("/api/auth/signup", methods=["POST"])
@auth_limiter.limit(f"{settings.api.rate_limit} per minute")
def create_user():
    user_data = request.get_json()
    return handle_create_user_request(user_data)

@auth_bp.route("/api/auth/verify", methods=["GET"])
def verify_user():
    token = request.args.get("token")
    return handle_verify_user_request(token)

@auth_bp.route("/api/auth/refresh", methods=["POST"])
@auth_limiter.limit("10 per minute")
@jwt_required()
def refresh_token():
    return handle_refresh_token_request(None)

@auth_bp.route("/api/auth/logout", methods=["POST"])
@auth_limiter.limit("10 per minute")
@jwt_required()
def logout():
    return handle_logout_request()

@auth_bp.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@auth_bp.route('/favicon.ico')
def favicon():
    return '', 204
