from typing import Optional
import requests
import logging
from .base import BaseService
from ..config.settings import Settings

class ApiClient(BaseService):
    """Client for interacting with the BrevioBot API."""

    def summarize(self, text: str, model: str, language: str) -> str:
        """
        Request text summarization from the API.
        
        Args:
            text: The text to summarize
            model: The AI model to use
            language: The target language

        Returns:
            str: The generated summary

        Raises:
            RuntimeError: If the API request fails
        """
        if model not in Settings.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        if language not in Settings.SUPPORTED_LANGUAGES:
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
