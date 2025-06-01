from flask import request, jsonify, g
from core.settings import settings
from calendarmgt.google.client import fetch_events, create_event, delete_event

def handle_fetch_events(req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    max_results = int(req.args.get('max_results', 10))
    creds_path = settings.google_client_secret.credentials_json
    events = fetch_events(user_id, calendar_id=calendar_id, max_results=max_results, creds_path=creds_path)
    return jsonify({'events': events})


def handle_create_event(req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    event_data = req.get_json()
    creds_path = settings.google_client_secret.credentials_json
    event = create_event(user_id, event_data, calendar_id=calendar_id, creds_path=creds_path)
    return jsonify({'event': event})


def handle_delete_event(event_id, req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    creds_path = settings.google_client_secret.credentials_json
    delete_event(user_id, event_id, calendar_id=calendar_id, creds_path=creds_path)
    return jsonify({'deleted': True})


def handle_list_calendars(req):
    user_id = g.current_user['user_id']
    creds_path = settings.google_client_secret.credentials_json
    from calendarmgt.google.auth import get_credentials_from_file
    from googleapiclient.discovery import build
    creds = get_credentials_from_file(user_id, creds_path)
    service = build('calendar', 'v3', credentials=creds)
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])
    return jsonify({'calendars': calendars})
