from googleapiclient.discovery import build
from .auth import get_credentials


def get_calendar_service():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    return service


def fetch_events(calendar_id='primary', max_results=10):
    service = get_calendar_service()
    events_result = service.events().list(calendarId=calendar_id, maxResults=max_results, singleEvents=True, orderBy='startTime').execute()
    return events_result.get('items', [])


def create_event(event, calendar_id='primary'):
    service = get_calendar_service()
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created_event


def delete_event(event_id, calendar_id='primary'):
    service = get_calendar_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return True