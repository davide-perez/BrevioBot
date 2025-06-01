from dataclasses import dataclass
from core.exceptions import ValidationError
from core.settings import settings
from core.logger import logger
from text.summarizers import TextSummarizer
from core.prompts import PROMPTS
from flask import jsonify, g
from openai import OpenAI
from calendars.google_handlers import handle_fetch_events
from toolcalls.prompts import INIT_GOOGLE_CALENDAR_TOOLCALL_PROMPT
from toolcalls.registry import dispatch_tool_call
from text.clients import LLMClientFactory
import json

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
    
@dataclass
class AskRequest:
    query: str
    model: str

    @classmethod
    def from_json(cls, data: dict) -> 'AskRequest':
        if not data.get("query"):
            raise ValidationError("Query field is required")
        if not data.get("model"):
            raise ValidationError("Model field is required")
        return cls(query=data["query"], model=data["model"])

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

def handle_ask_request(request_json):
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing ask request{user_info}")

    request_data = AskRequest.from_json(request_json or {})

    system_prompt = INIT_GOOGLE_CALENDAR_TOOLCALL_PROMPT
    api_key = settings.app.openai_api_key
    if not api_key:
        raise ValidationError("OpenAI API key is required for this call")

    try:
        client = LLMClientFactory.create(request_data.model, system_prompt, api_key)
    except Exception as e:
        logger.error(f"Failed to create LLM client: {e}", exc_info=True)
        raise ValidationError(str(e))

    try:
        response = client.call(request_data.query)
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        raise ValidationError("LLM did not return a valid response.")

    try:
        tool_call = json.loads(response)
        tool_name = tool_call["tool_name"]
        parameters = tool_call["parameters"]
    except Exception as e:
        logger.error(f"Failed to parse tool-call JSON: {response}", exc_info=True)
        raise ValidationError("LLM did not return a valid tool-call JSON.")

    try:
        result = dispatch_tool_call(tool_name, parameters)
    except Exception as e:
        logger.error(f"Tool-call dispatch failed: {e}", exc_info=True)
        raise ValidationError(f"Tool-call dispatch failed: {e}")

    logger.info(f"Successfully handled ask request{user_info}")
    return jsonify(result)
