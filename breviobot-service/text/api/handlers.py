from dataclasses import dataclass
from core.exceptions import ValidationError
from core.settings import settings
from core.logger import logger
from text.summarizers import TextSummarizer
from core.prompts import PROMPTS
from flask import jsonify, g

@dataclass
class SummarizeRequest:
    text: str
    language: str
    model: str

    @classmethod
    def from_json(cls, data: dict) -> 'SummarizeRequest':
        if not data.get("text"):
            raise ValidationError("Text field is required")
        
        if len(data["text"]) > settings.app.max_input_length:
            raise ValidationError(f"Text exceeds maximum length of {settings.app.max_input_length}")
        
        return cls(
            text=data["text"],
            language=data.get("language", settings.app.default_language),
            model=data.get("model", settings.app.default_model)
        )

def handle_summarize_request(request_json):
    request_data = SummarizeRequest.from_json(request_json or {})
    
    if request_data.model.startswith("gpt") and not settings.is_openai_configured():
        raise ValidationError("OpenAI API key not configured for GPT models")
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing summarization request{user_info} for language: {request_data.language}, model: {request_data.model}")
    
    summarizer = TextSummarizer(settings.app.openai_api_key, PROMPTS)
    result = summarizer.summarize_text(
        request_data.text,
        request_data.model,
        request_data.language
    )
    
    logger.info(f"Successfully generated summary{user_info}")
    return jsonify({"summary": result})