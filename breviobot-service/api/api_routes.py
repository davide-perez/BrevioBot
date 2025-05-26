from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from core.settings import settings
from core.exceptions import BrevioBotError, ValidationError, RateLimitError, ConfigurationError
from core.logger import logger
from .api_handlers import (
    handle_breviobot_error,
    handle_general_error,
    handle_summarize_request,
    handle_transcribe_request,
    handle_authentication_error,
    handle_create_user_request,
    handle_login_request,
)
from auth.auth_handlers import (
    handle_refresh_token_request, 
    handle_logout_request, 
    handle_me_request
)
from auth.auth_exceptions import AuthenticationError
from auth.auth_service import require_auth

app = Flask(__name__)
CORS(app, origins=settings.api.cors_origins)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

# Error handlers
app.errorhandler(BrevioBotError)(handle_breviobot_error)
app.errorhandler(AuthenticationError)(handle_authentication_error)
app.errorhandler(Exception)(handle_general_error)

# Authentication routes
@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    try:
        return handle_login_request(request.get_json())
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return {"error": "Login failed"}, 500

@app.route("/api/auth/refresh", methods=["POST"])
@limiter.limit("10 per minute")
def refresh_token():
    try:
        return handle_refresh_token_request(request.get_json())
    except (ValidationError, AuthenticationError) as e:
        return handle_authentication_error(e)
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        return {"error": "Token refresh failed"}, 500

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    try:
        return handle_logout_request()
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return {"error": "Logout failed"}, 500

@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    try:
        return handle_me_request()
    except AuthenticationError as e:
        return handle_authentication_error(e)
    except Exception as e:
        logger.error(f"User info error: {str(e)}", exc_info=True)
        return {"error": "Failed to get user info"}, 500

# Service routes
@app.route("/api/summarize", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def summarize():
    try:
        return handle_summarize_request(request.json)
    except ValidationError as e:
        logger.warning(f"Validation error in summarize: {str(e)}")
        return {"error": str(e)}, 400
    except ConfigurationError as e:
        logger.error(f"Configuration error in summarize: {str(e)}")
        return {"error": str(e)}, 500
    except AuthenticationError as e:
        return handle_authentication_error(e)
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in summarize: {str(e)}")
        return {"error": str(e)}, 429
    except Exception as e:
        logger.error(f"Unexpected error in summarize: {str(e)}", exc_info=True)
        return {"error": f"Failed to process summarization: {str(e)}"}, 500

@app.route("/api/transcribe", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def transcribe():
    try:
        return handle_transcribe_request(request.files, request.form)
    except ValidationError as e:
        logger.warning(f"Validation error in transcribe: {str(e)}")
        return {"error": str(e)}, 400
    except ConfigurationError as e:
        logger.error(f"Configuration error in transcribe: {str(e)}")
        return {"error": str(e)}, 500
    except AuthenticationError as e:
        return handle_authentication_error(e)
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded in transcribe: {str(e)}")
        return {"error": str(e)}, 429
    except Exception as e:
        logger.error(f"Unexpected error in transcribe: {str(e)}", exc_info=True)
        return {"error": f"Failed to process transcription: {str(e)}"}, 500

@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}, 200

# User


@app.route("/api/users", methods=["GET"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
def get_users():
    try:
        # Placeholder for user retrieval logic
        return {"message": "User retrieval not implemented"}, 501
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}", exc_info=True)
        return {"error": "Failed to retrieve users"}, 500
    
@app.route("/api/users", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
def create_user():
    try:
        user_data = request.get_json()
        return handle_create_user_request(user_data)
    except ValidationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        return {"error": "Failed to create user"}, 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)
