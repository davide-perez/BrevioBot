import os
from pathlib import Path
import openai
from faster_whisper import WhisperModel
from abc import ABC, abstractmethod

class AbstractTranscriber(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        pass


class WhisperLocalTranscriber(AbstractTranscriber):
    def __init__(self, model_size="base"):
        super().__init__()
        self.model = WhisperModel(model_size, device="auto", compute_type="auto")

    def transcribe(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        segments, _ = self.model.transcribe(str(audio_path))
        return " ".join([segment.text for segment in segments])



class WhisperAPITranscriber(AbstractTranscriber):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        openai.api_key = self.api_key

    def transcribe(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            result = openai.Audio.transcribe("whisper-1", audio_file)
            return result["text"]