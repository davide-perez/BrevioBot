from flask import jsonify, g
from core.settings import settings
from calendars.google_client import fetch_events, create_event, delete_event
from calendars.utils import parse_date_formula, is_date_formula
from core.logger import logger
from toolcalls.registry import register_tool

def fetch_events_for_user(user_id, start_date, end_date, calendar_id='primary', max_results=20):
    creds_path = settings.google_client_secret.credentials_json
    events = fetch_events(
        user_id,
        calendar_id=calendar_id,
        max_results=max_results,
        creds_path=creds_path,
        time_min=start_date,
        time_max=end_date
    )
    return events


def handle_fetch_events(req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    max_results = int(req.args.get('max_results', 10))
    time_min = req.args.get('time_min')
    time_max = req.args.get('time_max')

    logger.info(f"[Calendar] Fetch events for user_id={user_id}, calendar_id={calendar_id}, max_results={max_results}, time_min={time_min}, time_max={time_max}")

    if is_date_formula(time_min):
        logger.info(f"[Calendar] Parsing time_min formula: {time_min}")
        time_min = parse_date_formula(time_min)
    if is_date_formula(time_max):
        logger.info(f"[Calendar] Parsing time_max formula: {time_max}")
        time_max = parse_date_formula(time_max)

    try:
        events = fetch_events_for_user(
            user_id,
            start_date=time_min,
            end_date=time_max,
            calendar_id=calendar_id,
            max_results=max_results
        )
        logger.info(f"[Calendar] Fetched {len(events)} events for user_id={user_id}")
        return jsonify({'events': events})
    except Exception as e:
        logger.error(f"[Calendar] Error fetching events for user_id={user_id}: {e}", exc_info=True)
        raise


def handle_create_event(req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    event_data = req.get_json()
    creds_path = settings.google_client_secret.credentials_json
    logger.info(f"[Calendar] Creating event for user_id={user_id}, calendar_id={calendar_id}")
    try:
        event = create_event(user_id, event_data, calendar_id=calendar_id, creds_path=creds_path)
        logger.info(f"[Calendar] Event created for user_id={user_id}, event_id={event.get('id')}")
        return jsonify({'event': event})
    except Exception as e:
        logger.error(f"[Calendar] Error creating event for user_id={user_id}: {e}", exc_info=True)
        raise


def handle_delete_event(event_id, req):
    user_id = g.current_user['user_id']
    calendar_id = req.args.get('calendar_id', 'primary')
    creds_path = settings.google_client_secret.credentials_json
    logger.info(f"[Calendar] Deleting event_id={event_id} for user_id={user_id}, calendar_id={calendar_id}")
    try:
        delete_event(user_id, event_id, calendar_id=calendar_id, creds_path=creds_path)
        logger.info(f"[Calendar] Event deleted: event_id={event_id} for user_id={user_id}")
        return jsonify({'deleted': True})
    except Exception as e:
        logger.error(f"[Calendar] Error deleting event_id={event_id} for user_id={user_id}: {e}", exc_info=True)
        raise


def handle_list_calendars(req):
    user_id = g.current_user['user_id']
    creds_path = settings.google_client_secret.credentials_json
    logger.info(f"[Calendar] Listing calendars for user_id={user_id}")
    try:
        from calendars.google_auth import get_credentials_from_file
        from googleapiclient.discovery import build
        creds = get_credentials_from_file(user_id, creds_path)
        service = build('calendar', 'v3', credentials=creds)
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        logger.info(f"[Calendar] Found {len(calendars)} calendars for user_id={user_id}")
        return jsonify({'calendars': calendars})
    except Exception as e:
        logger.error(f"[Calendar] Error listing calendars for user_id={user_id}: {e}", exc_info=True)
        raise


@register_tool("get_google_calendar_events")
def get_google_calendar_events(start_date: str, end_date: str, calendar_id: str = 'primary', max_results: int = 20):
    """
    Tool-callable function to fetch Google Calendar events for the current user between start_date and end_date.
    Returns only essential info: summary, start, end, is_recurring, htmlLink.
    """
    user_id = g.current_user['user_id']
    events = fetch_events_for_user(
        user_id,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        max_results=max_results
    )
    filtered = []
    for e in events:
        filtered.append({
            'summary': e.get('summary'),
            'date_start': e.get('start', {}).get('dateTime'),
            'date_end': e.get('end', {}).get('dateTime'),
            'is_recurring': 'recurringEventId' in e,
            'htmlLink': e.get('htmlLink')
        })
    return {'events': filtered}
