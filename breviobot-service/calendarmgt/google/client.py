from googleapiclient.discovery import build
from .auth import get_credentials_from_file, get_credentials_from_json
from core.settings import settings


def get_calendar_service(user_id, creds_path=None, creds_json_string=None):
    if creds_path is None and creds_json_string is None:
        creds_path = getattr(settings.google_client_secret, 'credentials_json', None)
    if creds_path:
        creds = get_credentials_from_file(user_id, creds_path)
    elif creds_json_string:
        creds = get_credentials_from_json(user_id, creds_json_string)
    else:
        raise ValueError("You must provide either creds_path or creds_json_string, or set settings.google_client_secret.credentials_json.")
    service = build('calendar', 'v3', credentials=creds)
    return service


def fetch_events(user_id, calendar_id='primary', max_results=10, creds_path=None, creds_json_string=None):
    service = get_calendar_service(user_id, creds_path, creds_json_string)
    events_result = service.events().list(calendarId=calendar_id, maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
    return events_result.get('items', [])


def create_event(user_id, event, calendar_id='primary', creds_path=None, creds_json_string=None):
    service = get_calendar_service(user_id, creds_path, creds_json_string)
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created_event


def delete_event(user_id, event_id, calendar_id='primary', creds_path=None, creds_json_string=None):
    service = get_calendar_service(user_id, creds_path, creds_json_string)
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return True