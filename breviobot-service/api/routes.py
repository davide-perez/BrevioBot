from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from core.settings import settings
from core.exceptions import BrevioBotError, ValidationError, RateLimitError
from core.logger import logger
from .handlers import handle_breviobot_error, handle_general_error, handle_summarize_request, handle_transcribe_request

app = Flask(__name__)
CORS(app, origins=settings.api.cors_origins)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

app.errorhandler(BrevioBotError)(handle_breviobot_error)
app.errorhandler(Exception)(handle_general_error)

@app.route("/api/summarize", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
def summarize():
    try:
        return handle_summarize_request(request.json)
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return {"error": str(e)}, 400
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {str(e)}")
        return {"error": str(e)}, 429
    

@app.route("/api/transcribe", methods=["POST"])
@limiter.limit(f"{settings.api.rate_limit} per minute")
def transcribe():
    try:
        return handle_transcribe_request(request.files, request.form)
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return {"error": str(e)}, 400
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {str(e)}")
        return {"error": str(e)}, 429
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return {"error": "Failed to process audio"}, 500


@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(debug=True, port=8000)
