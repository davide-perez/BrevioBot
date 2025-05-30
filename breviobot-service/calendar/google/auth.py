import os
import json
from core.settings import settings
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials():
    """Gets valid user credentials from storage or runs the OAuth2 flow."""
    creds = None
    token_path = settings.google_calendar.token_pickle
    # Write credentials to a temp file if needed
    creds_json = settings.google_calendar.credentials_json
    if os.path.isfile(creds_json):
        creds_path = creds_json
    else:
        creds_path = 'google_credentials_tmp.json'
        with open(creds_path, 'w') as f:
            f.write(creds_json)
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    # Clean up temp file if used
    if creds_path == 'google_credentials_tmp.json' and os.path.exists(creds_path):
        os.remove(creds_path)
    return creds