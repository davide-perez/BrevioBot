from typing import List
from pydantic import BaseModel, Field
from datetime import datetime
import json
from agents import Agent, Runner, function_tool
from flask import g
from calendars.google_handlers import fetch_events_for_user
from core.logger import logger

CALENDAR_AGENT_PROMPT = (
    "You are an intelligent assistant for calendar event management. "
    "Handle requests to create, update, delete, or retrieve events. "
    "Each event includes a title, start date, end date, recurrence flag, and HTML link."
    "Always use dates in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). "
    "Respond clearly and concisely, yet informally. Include the summary of the fetched events."
    f"Today's date is {datetime.now().isoformat()}. When interpreting natural language queries involving relative dates (e.g., “next week”), assume this as the current date."
    "Request any missing information needed to complete the operation."
)

class CalendarQueryResult(BaseModel):
    """
    Represents a result of a calendar query.
    """
    summary: str = Field(description="A description of all the events fetched from the calendar")
    events: List[str] = Field(description="List of events associated with the calendar query")
    from_date: datetime = Field(description="The start date of the calendar query")
    to_date: datetime = Field(description="The end date of the calendar query")

    def __str__(self):
        return f"{self.summary} from {self.from_date} to {self.to_date}"


@function_tool
def get_google_calendar_events(start_date: str, end_date: str) -> str:
    """
    Tool-callable function to fetch Google Calendar events for the current user between start_date and end_date.
    """
    try:
        user_id = g.current_user['user_id']
        events = fetch_events_for_user(
            user_id,
            start_date=start_date,
            end_date=end_date,
            calendar_id='primary',
            max_results=50
        )
        filtered = []
        for e in events:
            filtered.append({
                'summary': e.get('summary'),
                'starting_date': e.get('start', {}).get('dateTime'),
                'ending_date': e.get('end', {}).get('dateTime'),
                'is_recurring': 'recurringEventId' in e,
                'html_link': e.get('htmlLink')
            })
        return json.dumps({'events': filtered})
    except Exception as ex:
        logger.error(f"Error in get_google_calendar_events: {ex}", exc_info=True)
        return json.dumps({
            'error': 'Failed to fetch calendar events. Please check your Google Calendar settings or permissions.'
        })