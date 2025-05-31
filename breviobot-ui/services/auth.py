import time
import base64
import json
import logging
import requests
import streamlit as st


class AuthService:
    GRACE_PERIOD_SECONDS = 60  # Refresh token 1 minute before expiry

    def __init__(self, config, access_token=None, refresh_token=None, sync_session=True):
        self.config = config
        self._sync_session = sync_session
        self.access_token = access_token
        self.refresh_token = refresh_token
        if self._sync_session:
            self._load_from_session()

    def _load_from_session(self):
        if 'access_token' in st.session_state:
            self.access_token = st.session_state.access_token
        if 'refresh_token' in st.session_state:
            self.refresh_token = st.session_state.refresh_token

    def _sync_to_session(self):
        if self._sync_session:
            st.session_state.access_token = self.access_token
            st.session_state.refresh_token = self.refresh_token

    def _decode_jwt_exp(self, token: str) -> int | None:
        try:
            payload_part = token.split(".")[1]
            padding = '=' * (-len(payload_part) % 4)
            payload_part += padding
            decoded = base64.urlsafe_b64decode(payload_part)
            payload = json.loads(decoded)
            return int(payload.get("exp"))
        except Exception:
            return None

    def _is_token_expired(self, token: str) -> bool:
        exp = self._decode_jwt_exp(token)
        if exp is None:
            return False
        return (exp - self.GRACE_PERIOD_SECONDS) < int(time.time())

    def is_access_token_expired(self) -> bool:
        return self._is_token_expired(self.access_token)

    def is_refresh_token_expired(self) -> bool:
        return self._is_token_expired(self.refresh_token)

    def get_token_exp_datetime(self, token: str) -> str | None:
        exp = self._decode_jwt_exp(token)
        if exp is None:
            return None
        return time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(exp))

    def get_access_token_exp_datetime(self) -> str | None:
        return self.get_token_exp_datetime(self.access_token)

    def get_refresh_token_exp_datetime(self) -> str | None:
        return self.get_token_exp_datetime(self.refresh_token)

    def set_tokens(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._sync_to_session()

    def logout(self):
        self.access_token = None
        self.refresh_token = None
        if self._sync_session:
            st.session_state.access_token = None
            st.session_state.refresh_token = None

    def refresh_access_token(self, refresh_token: str = None) -> None:
        token = refresh_token or self.refresh_token
        if not token:
            self.logout()
            raise Exception("No refresh token available.")
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/auth/refresh",
                headers={"Authorization": f"Bearer {token}"}
            )
            try:
                data = response.json()
            except Exception:
                data = None
            if response.ok and data and "access_token" in data:
                self.access_token = data["access_token"]
                if "refresh_token" in data:
                    self.refresh_token = data["refresh_token"]
                self._sync_to_session()
            else:
                self.logout()
                raise Exception(data.get("error", "Failed to refresh token"))
        except requests.exceptions.RequestException as e:
            self.logout()
            raise Exception(f"Refresh token request failed: {str(e)}")

    def ensure_valid_access_token(self) -> tuple[str, str]:
        if not self.access_token:
            raise Exception("No access token set.")
        if self.is_access_token_expired() and self.refresh_token:
            self.refresh_access_token(self.refresh_token)
        return self.access_token, self.refresh_token