from typing import Dict, Optional
from gtts import gTTS
import os
import tempfile
from pathlib import Path
from .base import BaseService
from ..config.settings import Settings

class TextToSpeechService(BaseService):
    """Service for text-to-speech conversion."""
    
    LANG_MAP: Dict[str, str] = {
        "it": "it",
        "en": "en"
    }

    def generate(self, text: str, lang_code: str) -> str:
        """
        Generate audio from text.
        
        Args:
            text: The text to convert to speech
            lang_code: The language code to use

        Returns:
            str: Path to the generated audio file
        """
        if lang_code not in Settings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {lang_code}")
            
        tts_lang = self.LANG_MAP.get(lang_code, "en")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=tts_lang)
            tts.save(temp_file.name)
            return temp_file.name

    @staticmethod
    def cleanup_file(file_path: str) -> None:
        """
        Clean up a generated audio file.
        
        Args:
            file_path: Path to the file to delete
        """
        try:
            os.unlink(file_path)
        except (OSError, FileNotFoundError):
            pass
