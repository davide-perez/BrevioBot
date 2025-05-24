from flask import jsonify
from dataclasses import dataclass
from typing import Optional

from summarizer.text import TextSummarizer
from core.prompts import PROMPTS
from core.settings import settings
from core.logger import logger
from core.exceptions import BrevioBotError, ValidationError, RateLimitError

@dataclass
class SummarizeRequest:
    text: str
    language: str
    model: str
    openai_api_key: Optional[str] = None

    @classmethod
    def from_json(cls, data: dict) -> 'SummarizeRequest':
        if not data.get("text"):
            raise ValidationError("Text field is required")
        
        if len(data["text"]) > settings.app.max_input_length:
            raise ValidationError(f"Text exceeds maximum length of {settings.app.max_input_length}")
        
        return cls(
            text=data["text"],
            language=data.get("language", settings.app.default_language),
            model=data.get("model", settings.app.default_model),
            openai_api_key=data.get("openai_api_key", settings.app.openai_api_key)
        )

def handle_breviobot_error(error):
    logger.error(f"BrevioBotError: {str(error)}")
    return jsonify({"error": str(error)}), 400

def handle_general_error(error):
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred"}), 500

def handle_summarize_request(request_json):
    request_data = SummarizeRequest.from_json(request_json or {})
    logger.info(f"Processing summarization request for language: {request_data.language}, model: {request_data.model}")
    
    summarizer = TextSummarizer(request_data.openai_api_key, PROMPTS)
    result = summarizer.summarize_text(
        request_data.text,
        request_data.model,
        request_data.language
    )
    
    logger.info("Successfully generated summary")
    return jsonify({"summary": result})
