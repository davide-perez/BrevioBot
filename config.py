import os
from dataclasses import dataclass, field
from typing import List, Literal
from dotenv import load_dotenv

@dataclass
class Config:
    DEFAULT_LANG: str
    DEFAULT_MODEL: str
    LOG_LEVEL: str
    OPENAI_API_KEY: str
    SUPPORTED_LANGUAGES: List[str] = field(default_factory=lambda: ["it", "en"])
    SUPPORTED_MODELS: List[str] = field(default_factory=lambda: ["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"])
    ModelType = Literal["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"]
    LangType = Literal["it", "en"]

    @classmethod
    def load(cls) -> 'Config':
        load_dotenv()
        return cls(
            DEFAULT_LANG=os.environ.get("DEFAULT_LANG", "it"),
            DEFAULT_MODEL=os.environ.get("DEFAULT_MODEL", "llama3"),
            LOG_LEVEL=os.environ.get("LOG_LEVEL", "ERROR"),
            OPENAI_API_KEY=os.environ.get("BREVIOBOT_OPENAI_API_KEY", "")
        )
