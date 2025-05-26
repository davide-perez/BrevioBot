from typing import Dict
from gtts import gTTS
import os
import tempfile
from pathlib import Path
from config.settings import AppDefaultSettings


class TextToSpeechServiceBase:
    def __init__(self, config):
        self.config = config


class TextToSpeechService(TextToSpeechServiceBase):
    LANG_MAP: Dict[str, str] = {
        "it": "it",
        "en": "en"
    }
    def generate(self, text: str, lang_code: str) -> str:
        if lang_code not in AppDefaultSettings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {lang_code}")
        tts_lang = self.LANG_MAP.get(lang_code, "en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=tts_lang)
            tts.save(temp_file.name)
            return temp_file.name
    @staticmethod
    def cleanup_file(file_path: str) -> None:
        try:
            os.unlink(file_path)
        except (OSError, FileNotFoundError):
            pass
