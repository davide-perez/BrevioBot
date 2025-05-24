import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

@dataclass
class AppConfig:
    openai_api_key: Optional[str]
    default_model: str
    default_language: str
    max_input_length: int
    request_timeout: int
    debug_mode: bool

@dataclass
class APIConfig:
    host: str
    port: int
    rate_limit: int
    cors_origins: list[str]

class Config:
    def __init__(self):
        load_dotenv()
        
        self.app = AppConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            default_model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
            default_language=os.getenv('DEFAULT_LANGUAGE', 'en'),
            max_input_length=int(os.getenv('MAX_INPUT_LENGTH', '4000')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
            debug_mode=os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        )
        
        self.api = APIConfig(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '8000')),
            rate_limit=int(os.getenv('RATE_LIMIT', '100')),
            cors_origins=os.getenv('CORS_ORIGINS', '*').split(',')
        )

config = Config()
