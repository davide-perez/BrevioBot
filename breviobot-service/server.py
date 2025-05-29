from auth.api.auth_api_routes import auth_bp, auth_limiter
from stt.api.stt_api_routes import stt_bp, stt_limiter
from text.api.text_api_routes import text_bp, text_limiter
from flask import Flask
from flask_cors import CORS
from core.settings import settings
from core.exceptions import ValidationError
from core.api_utils import (
    handle_validation_error,
    handle_general_error,
    handle_authentication_error
)
from core.exceptions import AuthenticationError

if __name__ == "__main__":
    app = Flask(__name__)
    CORS(app, origins=settings.api.cors_origins)

    auth_limiter.init_app(app)
    stt_limiter.init_app(app)
    text_limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(stt_bp)
    app.register_blueprint(text_bp)

    app.errorhandler(AuthenticationError)(handle_authentication_error)
    app.errorhandler(ValidationError)(handle_validation_error)
    app.errorhandler(Exception)(handle_general_error)
    app.run(host="0.0.0.0", port=8000, debug=True)
