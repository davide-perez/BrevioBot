from openai import OpenAI
import subprocess
from core.exceptions import ValidationError, ModelError
from core.logger import logger

class LLMClientBase:
    def __init__(self, model: str, system_prompt: str):
        self.model = model
        self.system_prompt = system_prompt

    def build_prompt(self, user_query: str) -> str:
        return self.system_prompt + f"\nUser query: {user_query}"

    def call(self, user_query: str) -> dict:
        raise NotImplementedError
    
    def is_supported_model(self) -> bool:
        raise NotImplementedError

class OpenAIClient(LLMClientBase):
    def __init__(self, api_key: str, model: str, system_prompt: str):
        super().__init__(model, system_prompt)
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def call(self, user_query: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}", exc_info=True)
            raise ValidationError("OpenAI did not return a valid response.")
        
    @staticmethod
    def is_supported_model(model: str) -> bool:
        # Retrieved with get https://api.openai.com/v1/models
        valid_models = [
            "gpt-4-1106-preview",
            "gpt-4o-audio-preview-2024-10-01",
            "gpt-4-turbo-preview",
            "gpt-4-turbo-2024-04-09",
            "gpt-4-turbo",
            "gpt-4",
            "chatgpt-4o-latest",
            "gpt-4o-mini-audio-preview",
            "gpt-4o-audio-preview",
            "gpt-4o-mini-realtime-preview",
            "gpt-4o-mini-realtime-preview-2024-12-17",
            "gpt-4.1-nano",
            "gpt-4.1-nano-2025-04-14",
            "gpt-3.5-turbo-instruct-0914",
            "gpt-3.5-turbo-16k",
            "gpt-4o-realtime-preview",
            "gpt-3.5-turbo-1106",
            "gpt-4o-search-preview",
            "gpt-3.5-turbo-instruct",
            "gpt-3.5-turbo",
            "gpt-4-0125-preview",
            "gpt-4o-2024-11-20",
            "gpt-4o-2024-05-13",
            "gpt-4-0613",
            "gpt-4o-mini-tts",
            "gpt-4o-transcribe",
            "gpt-4.5-preview",
            "gpt-4.5-preview-2025-02-27",
            "gpt-4o-search-preview-2025-03-11",
            "gpt-4o",
            "gpt-4o-2024-08-06",
            "gpt-4o-mini-2024-07-18",
            "gpt-4.1-mini",
            "gpt-4o-mini",
            "gpt-4o-mini-audio-preview-2024-12-17",
            "gpt-3.5-turbo-0125",
            "gpt-4o-realtime-preview-2024-10-01",
            "gpt-4o-mini-transcribe",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4.1",
            "gpt-4.1-2025-04-14",
            "gpt-4o-audio-preview-2024-12-17",
            "gpt-4o-realtime-preview-2024-12-17"
        ]
        return model.lower() in [m.lower() for m in valid_models]

class OllamaClient(LLMClientBase):
    def __init__(self, model: str, system_prompt: str):
        super().__init__(model, system_prompt)

    def call(self, user_query: str) -> str:
        prompt = f"[SYSTEM]\n{self.system_prompt}\n[USER]\n{user_query}"
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode != 0:
                logger.error(f"Ollama error: {result.stderr.decode('utf-8')}")
                raise ModelError(f"Ollama error: {result.stderr.decode('utf-8')}")
            return result.stdout.decode("utf-8").strip()
        except Exception as e:
            logger.error(f"Ollama error: {e}", exc_info=True)
            raise ValidationError("Ollama did not return a valid response.")
        
    @staticmethod
    def is_supported_model(model: str) -> bool:
        return model.lower() in ["llama3"]
        
class LLMClientFactory:
    @staticmethod
    def create(model: str, system_prompt: str, api_key: str = None):
        if OpenAIClient.is_supported_model(model):
            if not api_key:
                raise ValueError("OpenAI API key required for GPT models")
            return OpenAIClient(api_key, model, system_prompt)
        if OllamaClient.is_supported_model(model):
            return OllamaClient(model, system_prompt)
        raise ValueError(
            f"Model '{model}' is not supported. "
            f"Supported OpenAI: {OpenAIClient.valid_models()}, "
            f"Supported Ollama: {OllamaClient.valid_models()}"
        )