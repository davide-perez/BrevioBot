from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from config.settings import Config, Settings

@dataclass
class AppState:
    config: Config
    current_text: str = ""
    summary: Optional[str] = None
    input_audio: Optional[bytes] = None
    summary_audio: Optional[bytes] = None
    lang: str = field(init=False)
    model: str = field(init=False)
    translations: Dict[str, Dict[str, str]] = field(init=False)
    T: Dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        self.lang = self.config.default_lang
        self.model = self.config.default_model
        self.translations = {}
        self.T = {}

    def reset_audio(self) -> None:
        self.input_audio = None
        self.summary_audio = None

    def reset_summary(self) -> None:
        self.summary = None
        self.summary_audio = None

    def set_translations(self, translations: Dict[str, Dict[str, str]]) -> None:
        self.translations = translations
        self._update_active_translation()

    def set_language(self, lang: str) -> None:
        if lang not in Settings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {lang}")
        self.lang = lang
        self._update_active_translation()

    def set_model(self, model: str) -> None:
        if model not in Settings.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        self.model = model

    def _update_active_translation(self) -> None:
        self.T = self.translations.get(self.lang, self.translations.get("en", {}))
