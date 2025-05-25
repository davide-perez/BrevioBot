import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

@dataclass
class AppSettings:
    openai_api_key: Optional[str]
    default_model: str
    default_language: str
    max_input_length: int
    request_timeout: int
    debug_mode: bool

@dataclass
class APISettings:
    host: str
    port: int
    rate_limit: int
    cors_origins: list[str]

@dataclass
class AudioSettings:
    temp_dir: str
    max_file_size: int
    allowed_formats: list[str]

@dataclass
class WhisperSettings:
    use_api: bool
    model_size: str

@dataclass 
class AuthSettings:
    secret_key: str
    token_expiry_hours: int
    enable_auth: bool

class Settings:
    def __init__(self):
        load_dotenv()
        
        self.app = AppSettings(
            openai_api_key=os.getenv('BREVIOBOT_OPENAI_API_KEY'),
            default_model=os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo'),
            default_language=os.getenv('DEFAULT_LANGUAGE', 'en'),
            max_input_length=int(os.getenv('MAX_INPUT_LENGTH', '4000')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
            debug_mode=os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        )
        
        self.api = APISettings(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '8000')),
            rate_limit=int(os.getenv('RATE_LIMIT', '100')),
            cors_origins=os.getenv('CORS_ORIGINS', '*').split(',')
        )
        
        self.audio = AudioSettings(
            temp_dir=os.getenv('AUDIO_TEMP_DIR', 'temp'),
            max_file_size=int(os.getenv('AUDIO_MAX_FILE_SIZE', '25')),  # MB
            allowed_formats=['mp3', 'wav', 'm4a', 'flac', 'ogg']        )
        
        self.whisper = WhisperSettings(
            use_api=os.getenv('WHISPER_USE_API', 'True').lower() == 'true',
            model_size=os.getenv('WHISPER_MODEL_SIZE', 'base')
        )
        
        self.auth = AuthSettings(
            secret_key=os.getenv('JWT_SECRET_KEY', 'temp'),
            token_expiry_hours=int(os.getenv('JWT_EXPIRY_HOURS', '24')),
            enable_auth=os.getenv('ENABLE_AUTH', 'true').lower() == 'true'
        )

    def validate_required_settings(self):
        errors = []
        
        if not self.app.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is required")
            
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
    
    def is_openai_configured(self) -> bool:
        return bool(self.app.openai_api_key)

settings = Settings()
