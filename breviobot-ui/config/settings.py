from dataclasses import dataclass
from typing import List, Literal
from pathlib import Path
from dotenv import load_dotenv
import os

@dataclass(frozen=True)
class AppDefaultSettings:
    SUPPORTED_LANGUAGES: List[str] = ("it", "en")
    SUPPORTED_MODELS: List[str] = ("llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4")
    ModelType = Literal["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"]
    LangType = Literal["it", "en"]
    DEFAULT_LANG: str = "it"
    DEFAULT_MODEL: str = "llama3"
    LOG_LEVEL: str = "ERROR"
    API_BASE_URL: str = "http://localhost:8000"
    LOG_DIR: Path = Path(__file__).parent.parent.parent / "log"

@dataclass
class AppSettings:
    default_lang: str
    default_model: str
    log_level: str
    api_base_url: str

    @classmethod
    def load(cls) -> 'AppSettings':
        load_dotenv()
        return cls(
            default_lang=os.environ.get("DEFAULT_LANG", AppDefaultSettings.DEFAULT_LANG),
            default_model=os.environ.get("DEFAULT_MODEL", AppDefaultSettings.DEFAULT_MODEL),
            log_level=os.environ.get("LOG_LEVEL", AppDefaultSettings.LOG_LEVEL),
            api_base_url=os.environ.get("API_BASE_URL", AppDefaultSettings.API_BASE_URL)
        )
