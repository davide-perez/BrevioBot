import datetime

# Get Google Calendar events between two dates (OpenAI Function Calling style)
TODAY = datetime.datetime.utcnow().date()

GET_GOOGLE_CALENDAR_EVENTS_SCHEMA = {
    "name": "get_google_calendar_events",
    "description": "Return all Google Calendar events between the specified start and end dates.",
    "parameters": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "format": "date-time",
                "description": "Start date and time (ISO 8601, e.g., 2025-06-01T00:00:00Z)"
            },
            "end_date": {
                "type": "string",
                "format": "date-time",
                "description": "End date and time (ISO 8601, e.g., 2025-06-07T23:59:59Z)"
            }
        },
        "required": ["start_date", "end_date"]
    }
}

INIT_GOOGLE_CALENDAR_TOOLCALL_PROMPT = (
    "You are an assistant that helps retrieve events between a start and end date from Google Calendar using structured tool-calls. "
    "When you receive a natural language request about calendar events, respond only with a JSON object that matches the function schema below, choosing the appropriate function and filling in the required parameters.\n"
    f"Today's date is {TODAY}. When interpreting natural language queries involving relative dates (e.g., “next week”), assume this as the current date.\n\n"
    f"Available function:\n{GET_GOOGLE_CALENDAR_EVENTS_SCHEMA}\n\n"
    "Example user request 1:\n"
    "\"Show me the calendar events between June 5 and June 7, 2025\"\n\n"
    "Example response 1:\n"
    "{\n"
    "  \"tool_name\": \"get_google_calendar_events\",\n"
    "  \"parameters\": {\n"
    "    \"start_date\": \"2025-06-05T00:00:00Z\",\n"
    "    \"end_date\": \"2025-06-07T23:59:59Z\"\n"
    "  }\n"
    "}\n\n"
    "Example user request 2:\n"
    "\"Show me the calendar events for this week\"\n\n"
    "Example response 2:\n"
    "{\n"
    "  \"tool_name\": \"get_google_calendar_events\",\n"
    "  \"parameters\": {\n"
    "    \"start_date\": \"2025-06-05T00:00:00Z\",\n"
    "    \"end_date\": \"2025-06-11T23:59:59Z\"\n"
    "  }\n"
    "}\n\n"
    "Always respond only with a JSON object matching this schema."
)

