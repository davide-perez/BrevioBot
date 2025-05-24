from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dataclasses import dataclass
from typing import Optional

from summarizer import TextSummarizer
from prompts import PROMPTS
from config import config
from logger import logger
from exceptions import BrevioBotError, ValidationError, RateLimitError

app = Flask(__name__)
CORS(app, origins=config.api.cors_origins)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{config.api.rate_limit} per minute"]
)

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
        
        if len(data["text"]) > config.app.max_input_length:
            raise ValidationError(f"Text exceeds maximum length of {config.app.max_input_length}")
        
        return cls(
            text=data["text"],
            language=data.get("language", config.app.default_language),
            model=data.get("model", config.app.default_model),
            openai_api_key=data.get("openai_api_key", config.app.openai_api_key)
        )

@app.errorhandler(BrevioBotError)
def handle_breviobot_error(error):
    logger.error(f"BrevioBotError: {str(error)}")
    return jsonify({"error": str(error)}), 400

@app.errorhandler(Exception)
def handle_general_error(error):
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred"}), 500

@app.route("/api/summarize", methods=["POST"])
@limiter.limit(f"{config.api.rate_limit} per minute")
def summarize():
    try:
        request_data = SummarizeRequest.from_json(request.json or {})
        logger.info(f"Processing summarization request for language: {request_data.language}, model: {request_data.model}")
        
        summarizer = TextSummarizer(request_data.openai_api_key, PROMPTS)
        result = summarizer.summarize_text(
            request_data.text,
            request_data.model,
            request_data.language
        )
        
        logger.info("Successfully generated summary")
        return jsonify({"summary": result})
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {str(e)}")
        return jsonify({"error": str(e)}), 429

if __name__ == "__main__":
    app.run(debug=True, port=8000)