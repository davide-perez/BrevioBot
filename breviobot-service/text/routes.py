from flask import Blueprint, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from core.settings import settings
from auth.authenticators import require_auth
from text.handlers import handle_summarize_request, handle_ask_request

text_bp = Blueprint("text", __name__)

text_limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

@text_bp.route("/api/text/summarize", methods=["POST"])
@text_limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def summarize():
    return handle_summarize_request(request.json)

@text_bp.route("/api/text/ask", methods=["POST"])
@text_limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def ask():
    return handle_ask_request(request.json)
