import requests
from typing import Optional
import logging

class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def summarize(self, text: str, model: str, language: str) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/api/summarize",
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
