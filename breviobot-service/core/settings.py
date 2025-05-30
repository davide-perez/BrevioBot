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
    database_url: str

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
    refresh_token_expiry_hours: int
    enable_auth: bool

@dataclass
class EmailSettings:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str

class Settings:
    def __init__(self) -> None:
        load_dotenv()
        
        self.app = AppSettings(
            openai_api_key=os.getenv('BREVIOBOT_OPENAI_API_KEY'),
            default_model=os.getenv('BREVIOBOT_DEFAULT_MODEL', 'gpt-3.5-turbo'),
            default_language=os.getenv('BREVIOBOT_DEFAULT_LANGUAGE', 'en'),
            max_input_length=int(os.getenv('BREVIOBOT_MAX_INPUT_LENGTH', '4000')),
            request_timeout=int(os.getenv('BREVIOBOT_REQUEST_TIMEOUT', '30')),
            debug_mode=os.getenv('BREVIOBOT_DEBUG_MODE', 'False').lower() == 'true',
            database_url=os.getenv('BREVIOBOT_DATABASE_URL', 'sqlite:///./breviobot.db')
        )

        self.api = APISettings(
            host=os.getenv('BREVIOBOT_HOST', '0.0.0.0'),            port=int(os.getenv('BREVIOBOT_PORT', '8000')),
            rate_limit=int(os.getenv('BREVIOBOT_RATE_LIMIT', '100')),
            cors_origins=os.getenv('BREVIOBOT_CORS_ORIGINS', '*').split(',')
        )
        
        self.audio = AudioSettings(
            temp_dir=os.getenv('BREVIOBOT_AUDIO_TEMP_DIR', 'temp'),
            max_file_size=int(os.getenv('BREVIOBOT_AUDIO_MAX_FILE_SIZE', '25')),  # MB
            allowed_formats=['mp3', 'wav', 'm4a', 'flac', 'ogg']
        )
        
        self.whisper = WhisperSettings(
            use_api=os.getenv('BREVIOBOT_WHISPER_USE_API', 'True').lower() == 'true',
            model_size=os.getenv('BREVIOBOT_WHISPER_MODEL_SIZE', 'base')
        )
        
        self.auth = AuthSettings(
            secret_key=os.getenv('BREVIOBOT_JWT_SECRET_KEY', ''),
            token_expiry_hours=int(os.getenv('BREVIOBOT_JWT_EXPIRY_HOURS', '24')),
            refresh_token_expiry_hours=int(os.getenv('BREVIOBOT_JWT_REFRESH_EXPIRY_HOURS', '168')),  # 7 days default
            enable_auth=os.getenv('BREVIOBOT_ENABLE_AUTH', 'true').lower() == 'true'
        )

        self.email = EmailSettings(
            smtp_host=os.getenv('BREVIOBOT_SMTP_HOST', ''),
            smtp_port=int(os.getenv('BREVIOBOT_SMTP_PORT', '587')),
            smtp_user=os.getenv('BREVIOBOT_SMTP_USER', ''),
            smtp_password=os.getenv('BREVIOBOT_SMTP_PASSWORD', ''),
            from_email=os.getenv('BREVIOBOT_EMAIL_FROM', ''),
            from_name=os.getenv('BREVIOBOT_EMAIL_FROM_NAME', 'BrevioBot')
        )

    def validate_required_settings(self) -> None:
        errors = []
        
        if not self.app.openai_api_key:
            errors.append("BREVIOBOT_OPENAI_API_KEY environment variable is required")
            
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
    
    def is_openai_configured(self) -> bool:
        return bool(self.app.openai_api_key)

settings = Settings()
