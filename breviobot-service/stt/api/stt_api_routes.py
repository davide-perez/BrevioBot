from flask import Blueprint, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from core.settings import settings
from auth.auth_service import require_auth
from stt.api.stt_api_handlers import handle_transcribe_request

stt_bp = Blueprint("stt", __name__)

stt_limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)


@stt_bp.route("/api/stt/transcribe", methods=["POST"])
@stt_limiter.limit(f"{settings.api.rate_limit} per minute")
@require_auth
def transcribe():
    return handle_transcribe_request(request.files, request.form)
