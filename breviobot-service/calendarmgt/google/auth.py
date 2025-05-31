import os
import json
from core.settings import settings
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from persistence.db_session import SessionLocal
from persistence.repositories import UserGoogleTokenRepository

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_credentials_from_file(user_id, creds_path):
    creds = None
    with SessionLocal() as db:
        repo = UserGoogleTokenRepository(db)
        token_blob = repo.get_token(user_id)
        if token_blob:
            creds = pickle.loads(token_blob)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            repo.set_token(user_id, pickle.dumps(creds))
    return creds


def get_credentials_from_json(user_id, creds_json_string):
    creds = None
    creds_path = 'google_credentials_tmp.json'
    with open(creds_path, 'w') as f:
        f.write(creds_json_string)
    try:
        creds = get_credentials_from_file(user_id, creds_path)
    finally:
        if os.path.exists(creds_path):
            os.remove(creds_path)
    return creds