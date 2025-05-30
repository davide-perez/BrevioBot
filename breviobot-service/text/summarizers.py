from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI
import subprocess
import os
from core.exceptions import ValidationError, ModelError
from core import settings
from core.logger import logger

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
            base_dir = os.getcwd()
            abs_path = os.path.abspath(path)
            if not abs_path.startswith(base_dir):
                logger.error(f"Attempted path traversal or access outside base dir: {path}")
                raise ValidationError("Invalid file path.")

            max_file_size = 5 * 1024 * 1024  # 5 MB
            if not os.path.exists(abs_path):
                logger.error(f"File not found: {abs_path}")
                raise ValidationError(f"File not found: {path}")
            file_size = os.path.getsize(abs_path)
            if file_size > max_file_size:
                logger.error(f"File too large: {abs_path} ({file_size} bytes)")
                raise ValidationError(f"File size exceeds maximum allowed size of {max_file_size // (1024*1024)}MB.")

            logger.info(f"Reading file for summarization: {abs_path}")
            with open(abs_path, "r", encoding="utf-8") as f:
                text = f.read()
            return self.summarize_text(text, model, lang)
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            raise ValidationError(f"File not found: {path}")
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}", exc_info=True)
            raise

class SummarizerBase(ABC):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    @abstractmethod
    def summarize(self, text: str) -> str:
        pass


class OllamaSummarizer(SummarizerBase):
    def __init__(self, system_prompt: str, model: str):
        super().__init__(system_prompt)
        self.model = model

    def summarize(self, text: str) -> str:
        full_prompt = f"{self.system_prompt}\n\n{text}"
        result = subprocess.run(
            ["ollama", "run", self.model],
            input=full_prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error in llama while summarizing: {result.stderr.decode('utf-8')}")
        return result.stdout.decode("utf-8").strip()
    

class OpenAISummarizer(SummarizerBase):
    def __init__(self, system_prompt: str, model: str, api_key: str):
        super().__init__(system_prompt)
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def summarize(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    

class SummarizerFactory:
    @staticmethod
    def create_summarizer(model: str, system_prompt: str, openai_api_key: str) -> SummarizerBase:
        if model.startswith("gpt"):
            if not openai_api_key:
                raise ValueError("OpenAI API key is not set")
            return OpenAISummarizer(system_prompt, model, openai_api_key)
        else:
            return OllamaSummarizer(system_prompt, model)