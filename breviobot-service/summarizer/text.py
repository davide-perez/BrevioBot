from dataclasses import dataclass
from typing import Optional
from core.exceptions import ValidationError, ModelError
from core.settings import settings
from core.logger import logger
from .summarization_services import SummarizerFactory

@dataclass
class SummaryRequest:
    text: str
    model: str
    lang: str
    max_length: Optional[int] = None

    def validate(self):
        if not self.text:
            raise ValidationError("Text cannot be empty")
        if len(self.text) > settings.app.max_input_length:
            raise ValidationError(f"Text exceeds maximum length of {settings.app.max_input_length}")
        if not self.model:
            raise ValidationError("Model must be specified")
        if not self.lang:
            raise ValidationError("Language must be specified")

class TextSummarizer:
    def __init__(self, openai_api_key: str, prompts: dict):
        self.openai_api_key = openai_api_key
        self.prompts = prompts
        self._validate_prompts()

    def _validate_prompts(self):
        if not self.prompts:
            raise ValidationError("Prompts dictionary cannot be empty")
        for lang, prompt in self.prompts.items():
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValidationError(f"Invalid prompt for language: {lang}")

    def summarize_text(self, text: str, model: str, lang: str, max_length: Optional[int] = None) -> str:
        try:
            request = SummaryRequest(text, model, lang, max_length)
            request.validate()
            
            if lang not in self.prompts:
                raise ValidationError(f"Prompt not available for language: {lang}")
            
            system_prompt = self.prompts[lang]
            logger.info(f"Summarizing text with model: {model}, language: {lang}")
            
            summarizer = SummarizerFactory.create_summarizer(
                model, system_prompt, self.openai_api_key
            )
            summary = summarizer.summarize(text)
            
            if not summary:
                raise ModelError("Model returned empty summary")
                
            logger.info("Successfully generated summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}", exc_info=True)
            raise

    def summarize_file(self, path: str, model: str, lang: str) -> str:
        try:
            logger.info(f"Reading file for summarization: {path}")
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            return self.summarize_text(text, model, lang)
            
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            raise ValidationError(f"File not found: {path}")
            
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}", exc_info=True)
            raise


