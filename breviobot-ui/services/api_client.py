from config.settings import AppDefaultSettings
import requests
import logging
from services.auth import AuthService

class ApiClientBase:
    def __init__(self, config):
        self.config = config

class ApiClient(ApiClientBase):
    def __init__(self, config):
        super().__init__(config)
        self.auth_service = AuthService(config)

    def login(self, username: str, password: str) -> tuple[bool, dict | None]:
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            try:
                data = response.json()
            except Exception:
                data = None

            if response.ok and data and not ("error" in data):
                return True, data
            else:
                return False, data
        except requests.exceptions.RequestException as e:
            logging.error(f"Login request failed: {str(e)}")
            return False, {"error": str(e)}

    def signup(self, username: str, email: str, password: str) -> tuple[bool, dict | None]:
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/auth/signup",
                json={"username": username, "email": email, "password": password}
            )
            try:
                data = response.json()
            except Exception:
                data = None

            if response.ok and data and not ("error" in data):
                return True, data
            else:
                return False, data
        except requests.exceptions.RequestException as e:
            logging.error(f"API signup failed: {str(e)}")
            return False, {"error": str(e)}

    def summarize(self, text: str, model: str, language: str) -> tuple[bool, dict | None]:
        if model not in AppDefaultSettings.SUPPORTED_MODELS:
            return False, {"error": f"Unsupported model: {model}"}
        if language not in AppDefaultSettings.SUPPORTED_LANGUAGES:
            return False, {"error": f"Unsupported language: {language}"}

        headers = {}
        if self.auth_service.access_token:
            headers["Authorization"] = f"Bearer {self.auth_service.access_token}"

        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/text/summarize",
                json={"text": text, "model": model, "language": language},
                headers=headers if headers else None
            )
            try:
                data = response.json()
            except Exception:
                data = None

            if response.ok and data and "summary" in data and not ("error" in data):
                return True, data
            else:
                return False, data
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            return False, {"error": str(e)}
