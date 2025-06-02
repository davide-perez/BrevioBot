from pydantic import BaseModel, Field
from datetime import datetime
import json
from agents import Agent, Runner, function_tool
from flask import g
from calendars.google_handlers import fetch_events_for_user

CALENDAR_AGENT_PROMPT = (
    "You are an intelligent assistant for calendar event management. "
    "Handle requests to create, update, delete, or retrieve events. "
    "Each event includes a numeric user id, title, start date, end date, recurrence flag, and HTML link. "
    "Respond clearly and concisely. Honor all provided details. "
    "Correctly process recurring and non-recurring events. "
    f"Today's date is {datetime.now().isoformat()}. When interpreting natural language queries involving relative dates (e.g., “next week”), assume this as the current date."
    "Request any missing information needed to complete the operation."
)

class CalendarEntry(BaseModel):
    """
    Represents a calendar entry with a summary, start date, and end date.
    """
    summary: str = Field(description="The description or title of the calendar entry")
    starting_date: datetime = Field(description="The start date of the calendar entry")
    ending_date: datetime = Field(description="The end date of the calendar entry")
    is_recurring: bool = Field(description="Whether the event is recurring")
    html_link: str = Field(description="A link to the event in a calendar application")

    def __str__(self):
        return f"{self.summary} from {self.starting_date} to {self.ending_date}"


@function_tool("get_google_calendar_events")
def get_google_calendar_events(start_date: str, end_date: str) -> str:
    """
    Tool-callable function to fetch Google Calendar events for the current user between start_date and end_date.
    Returns only essential info: summary, start, end, is_recurring, htmlLink.
    """
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