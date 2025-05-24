from summarizer.ollama import OllamaSummarizer
from summarizer.openai import OpenAISummarizer
from summarizer.base import SummarizerBase

class SummarizerFactory:
    @staticmethod
    def create_summarizer(model: str, system_prompt: str, openai_api_key: str) -> SummarizerBase:
        if model.startswith("gpt"):
            if not openai_api_key:
                raise ValueError("OpenAI API key is not set")
            return OpenAISummarizer(system_prompt, model, openai_api_key)
        else:
            return OllamaSummarizer(system_prompt, model)