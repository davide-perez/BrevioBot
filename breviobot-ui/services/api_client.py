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
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

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

    def refresh_access_token(self, refresh_token: str) -> tuple[bool, dict | None]:
        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/auth/refresh",
                headers={"Authorization": f"Bearer {refresh_token}"}
            )
            try:
                data = response.json()
            except Exception:
                data = None
            if response.ok and data and "access_token" in data:
                return True, data
            else:
                return False, data
        except requests.exceptions.RequestException as e:
            logging.error(f"Refresh token request failed: {str(e)}")
            return False, {"error": str(e)}

# TODO: store and use expiration dates to refresh the token
    def ensure_valid_access_token(self, access_token: str, refresh_token: str) -> tuple[str, str]:
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(f"{self.config.api_base_url}/api/auth/me", headers=headers)
        except Exception as e:
            logging.error(f"Token validation request failed: {str(e)}")
            raise
        if response.status_code == 200:
            return access_token, refresh_token
        elif response.status_code == 401 and refresh_token:
            success, data = self.refresh_access_token(refresh_token)
            if success:
                new_access_token = data.get("access_token")
                return new_access_token, refresh_token
            else:
                raise Exception(data.get("error", "Failed to refresh token"))
        else:
            raise Exception("Authentication failed.")
