from flask import Blueprint, request, jsonify, g
from auth.authenticators import require_auth
from calendars.google.handlers import handle_fetch_events, handle_create_event, handle_delete_event, handle_list_calendars
from core.settings import settings
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

calendar_bp = Blueprint("calendar_api", __name__)
calendar_limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=[f"{settings.api.rate_limit} per minute"]
)

@calendar_bp.route("/api/calendar/events", methods=["GET"])
@require_auth
@calendar_limiter.limit("5 per minute")
def fetch_events():
    return handle_fetch_events(request)

@calendar_bp.route("/api/calendar/events", methods=["POST"])
@require_auth
@calendar_limiter.limit("5 per minute")
def create_event():
    return handle_create_event(request)

@calendar_bp.route("/api/calendar/events/<event_id>", methods=["DELETE"])
@require_auth
@calendar_limiter.limit("5 per minute")
def delete_event(event_id):
    return handle_delete_event(event_id, request)

@calendar_bp.route("/api/calendar/list", methods=["GET"])
@require_auth
@calendar_limiter.limit("5 per minute")
def list_calendars():
    return handle_list_calendars(request)
