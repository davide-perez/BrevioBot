from auth.routes import auth_bp, auth_limiter
from stt.routes import stt_bp, stt_limiter
from text.routes import text_bp, text_limiter
from calendars.google_routes import calendar_bp, calendar_limiter
from flask import Flask, jsonify
from flask_cors import CORS
from core.settings import settings
from core.exceptions import ValidationError
from core.api_utils import (
    handle_validation_error,
    handle_general_error,
    handle_authentication_error
)
from core.exceptions import AuthenticationError
from flask_jwt_extended import JWTManager
from datetime import timedelta

if __name__ == "__main__":
    app = Flask(__name__)
    CORS(app, origins=settings.api.cors_origins)

    jwt = JWTManager(app)
    app.config["JWT_SECRET_KEY"] = settings.auth.secret_key
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=settings.auth.token_expiry_minutes)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(minutes=settings.auth.refresh_token_expiry_minutes)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization token is required"}), 401

    auth_limiter.init_app(app)
    stt_limiter.init_app(app)
    text_limiter.init_app(app)
    calendar_limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(stt_bp)
    app.register_blueprint(text_bp)
    app.register_blueprint(calendar_bp)

    app.errorhandler(AuthenticationError)(handle_authentication_error)
    app.errorhandler(ValidationError)(handle_validation_error)
    app.errorhandler(Exception)(handle_general_error)
    app.run(host="0.0.0.0", port=8000, debug=True)
