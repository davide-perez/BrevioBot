import tempfile
from typing import Dict
from gtts import gTTS
import os

class TextToSpeech:
    LANG_MAP: Dict[str, str] = {
        "it": "it",
        "en": "en"
    }

    @staticmethod
    def generate(text: str, lang_code: str) -> str:
        tts_lang = TextToSpeech.LANG_MAP.get(lang_code, "en")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=tts_lang)
            tts.save(temp_file.name)
            return temp_file.name

    @staticmethod
    def cleanup_file(file_path: str):
        try:
            os.unlink(file_path)
        except (OSError, FileNotFoundError):
            pass
