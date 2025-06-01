from dataclasses import dataclass
from core.exceptions import ValidationError
from core.settings import settings
from core.logger import logger
from text.summarizers import TextSummarizer
from core.prompts import PROMPTS
from flask import jsonify, g
from openai import OpenAI
from calendars.google_handlers import handle_fetch_events

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
    text = request_json.get("text")
    if not text:
        raise ValidationError("Text field is required")
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing ask request{user_info}: {text}")

    # Prompt per classificare l'intento
    system_prompt = (
        "Se la domanda riguarda il calendario (es. eventi, appuntamenti, impegni, riunioni), "
        "rispondi solo con 'calendar' e indica il periodo (es. 'next week', 'oggi', 'domani', 'dal 1 al 5 giugno'). "
        "Altrimenti rispondi 'other'.\nDomanda: " + text
    )
    client = OpenAI(api_key=settings.app.openai_api_key)
    response = client.chat.completions.create(
        model=settings.app.default_model,
        messages=[{"role": "system", "content": system_prompt}],
        temperature=0.0
    )
    content = response.choices[0].message.content.strip().lower()
    if content.startswith("calendar"):
        # Estrai periodo (es. 'next week', 'oggi', ecc.)
        import re
        match = re.search(r"calendar(?:[:\-]?\s*)(.*)", content)
        period = match.group(1).strip() if match and match.group(1) else ""
        # Mappa periodo in time_min/time_max (esempio: 'next week' -> time_min/today, time_max/+7D)
        # Qui esempio semplice: se 'next week' -> time_min='+7D', time_max='+14D'
        time_min, time_max = None, None
        if "next week" in period:
            time_min = "+7D"
            time_max = "+14D"
        elif "questa settimana" in period or "this week" in period:
            time_min = "+0D"
            time_max = "+7D"
        elif "oggi" in period or "today" in period:
            time_min = "+0D"
            time_max = "+1D"
        # Altri casi da gestire...
        # Costruisci una finta request per handle_fetch_events
        class DummyReq:
            args = {"time_min": time_min, "time_max": time_max}
        return handle_fetch_events(DummyReq())
    else:
        return jsonify({"result": "Non so come rispondere a questa domanda."})