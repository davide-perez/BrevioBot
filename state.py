from dataclasses import dataclass, field
from typing import Optional
from config import Config
from translations import UI

@dataclass
class AppState:
    config: Config
    current_text: str = ""
    summary: Optional[str] = None
    input_audio: Optional[bytes] = None
    summary_audio: Optional[bytes] = None
    lang: str = field(init=False)
    model: str = field(init=False)
    T: dict = field(init=False)

    def __post_init__(self):
        self.lang = self.config.DEFAULT_LANG
        self.model = self.config.DEFAULT_MODEL
        self.T = {}
        self.set_translation(UI)  # Initialize translations with default language

    def reset_audio(self):
        self.input_audio = None
        self.summary_audio = None

    def reset_summary(self):
        self.summary = None
        self.summary_audio = None

    def set_translation(self, translations: dict):
        self.T = translations[self.lang]

    def set_language(self, lang: str, translations: dict):
        self.lang = lang
        self.set_translation(translations)

    def set_model(self, model: str):
        self.model = model
