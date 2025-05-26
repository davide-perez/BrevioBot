from config.settings import AppDefaultSettings
import requests
import logging

class ApiClientBase:
    def __init__(self, config):
        self.config = config


class ApiClient(ApiClientBase):
    def summarize(self, text: str, model: str, language: str) -> str:
        if model not in AppDefaultSettings.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        if language not in AppDefaultSettings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        try:
            response = requests.post(
                f"{self.config.api_base_url}/api/summarize",
                json={"text": text, "model": model, "language": language}
            )
            response.raise_for_status()
            return response.json()["summary"]
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            raise RuntimeError(f"Failed to contact the server: {str(e)}")
        except KeyError as e:
            logging.error(f"Unexpected API response format: {str(e)}")
            raise RuntimeError("Unexpected response from server")
