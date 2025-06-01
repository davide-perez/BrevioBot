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
    """
    Handles a natural language query, sends it to the LLM for tool-call, and dispatches the tool call if present.
    """
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing ask request{user_info}")

    # 1. Estrarre la query utente
    query = request_json.get("query")
    if not query:
        raise ValidationError("Missing 'query' in request body")

    # 2. Inizializzare il prompt per l'LLM
    prompt = INIT_GOOGLE_CALENDAR_TOOLCALL_PROMPT + f"\nUser query: {query}"

    # 3. Chiamare il LLM (esempio con OpenAI, da adattare per Ollama se serve)
    client = OpenAI(api_key=settings.app.openai_api_key)
    response = client.chat.completions.create(
        model=settings.app.default_model,
        messages=[{"role": "system", "content": prompt}],
        temperature=0
    )
    llm_output = response.choices[0].message.content.strip()

    # 4. Estrarre il tool-call dal JSON generato dal LLM
    try:
        tool_call = json.loads(llm_output)
        tool_name = tool_call["tool_name"]
        parameters = tool_call["parameters"]
    except Exception as e:
        logger.error(f"Failed to parse tool-call JSON: {llm_output}", exc_info=True)
        raise ValidationError("LLM did not return a valid tool-call JSON.")

    # 5. Dispatch tool-call
    try:
        result = dispatch_tool_call(tool_name, parameters)
    except Exception as e:
        logger.error(f"Tool-call dispatch failed: {e}", exc_info=True)
        raise ValidationError(f"Tool-call dispatch failed: {e}")

    logger.info(f"Successfully handled ask request{user_info}")
    return jsonify(result)
