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
        """Convert text to speech using Google Text-to-Speech.
        
        Args:
            text (str): The text to convert to speech
            lang_code (str): Language code (it/en)
        
        Returns:
            str: Path to the temporary audio file
        """
        tts_lang = TextToSpeech.LANG_MAP.get(lang_code, "en")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts = gTTS(text=text, lang=tts_lang)
            tts.save(temp_file.name)
            return temp_file.name

    @staticmethod
    def cleanup_file(file_path: str):
        """Remove the temporary audio file after use."""
        try:
            os.unlink(file_path)
        except (OSError, FileNotFoundError):
            pass
