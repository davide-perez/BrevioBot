from config.settings import AppDefaultSettings
import requests
import logging

class ApiClientBase:
    def __init__(self, config, access_token: str = None):
        self.config = config
        self.access_token = access_token

class ApiClient(ApiClientBase):
    def login(self, username: str, password: str) -> tuple[bool, dict | None]:
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            try:
                data = response.json()
            except Exception:
                data = None
            return response.status_code == 200, data
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            raise RuntimeError(f"Authentication failed: {str(e)}")

    def summarize(self, text: str, model: str, language: str) -> str:
        if model not in AppDefaultSettings.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        if language not in AppDefaultSettings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/summarize",
                json={"text": text, "model": model, "language": language},
                headers=headers if headers else None
            )
            response.raise_for_status()
            return response.json()["summary"]
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            raise RuntimeError(f"Failed to contact the server: {str(e)}")
        except KeyError as e:
            logging.error(f"Unexpected API response format: {str(e)}")
            raise RuntimeError("Unexpected response from server")
