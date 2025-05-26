import os
from pathlib import Path
import openai
from faster_whisper import WhisperModel
from abc import ABC, abstractmethod
from core.settings import settings
from core.logger import logger

class AbstractTranscriber(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        pass


class WhisperLocalTranscriber(AbstractTranscriber):
    def __init__(self, model_size="base"):
        super().__init__()

        device_configs = [
            ("cuda", "float16"),
            ("cpu", "int8")
        ]
        
        self.model = None
        self.model_size = model_size
        for device, compute_type in device_configs:
            try:
                self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
                print(f"Whisper initialized with {device.upper()} acceleration ({compute_type})")
                break
            except Exception as e:
                print(f"Failed to initialize with {device}: {str(e)}")
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['cuda', 'cublas', 'cudnn', 'dll']):
                    print(f"CUDA library issue detected, trying next configuration...")
                continue
        if self.model is None:
            raise RuntimeError("Failed to initialize Whisper with any device configuration")

    def transcribe(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            segments, _ = self.model.transcribe(str(audio_path))
            return " ".join([segment.text for segment in segments])
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['cuda', 'cublas', 'cudnn', 'dll']):
                logger.warning(f"CUDA runtime error during transcription: {e}")
                logger.info("Reinitializing with CPU fallback...")
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                logger.info("Reinitialized with CPU, retrying transcription...")
                segments, _ = self.model.transcribe(str(audio_path))
                return " ".join([segment.text for segment in segments])
            else:
                logger.error(f"Error during local transcription: {e}", exc_info=True)
                raise



class WhisperAPITranscriber(AbstractTranscriber):
    def __init__(self):
        super().__init__()
        if not settings.is_openai_configured():
            raise ValueError("BREVIOBOT_OPENAI_API_KEY environment variable not configured - set BREVIOBOT_OPENAI_API_KEY environment variable")
        self.api_key = settings.app.openai_api_key
        openai.api_key = self.api_key

    def transcribe(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            with open(audio_path, "rb") as audio_file:
                result = openai.Audio.transcribe("whisper-1", audio_file)
                return result["text"]
        except Exception as e:
            logger.error(f"Error during API transcription: {e}", exc_info=True)
            raise