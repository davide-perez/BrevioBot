from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from ..config.settings import Config, Settings

@dataclass
class AppState:
    """
    Application state management class.
    Handles the application's runtime state and configuration.
    """
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
        """Initialize default values after instance creation."""
        self.lang = self.config.default_lang
        self.model = self.config.default_model
        self.translations = {}
        self.T = {}

    def reset_audio(self) -> None:
        """Reset all audio-related state."""
        self.input_audio = None
        self.summary_audio = None

    def reset_summary(self) -> None:
        """Reset summary-related state."""
        self.summary = None
        self.summary_audio = None

    def set_translations(self, translations: Dict[str, Dict[str, str]]) -> None:
        """
        Set the available translations.
        
        Args:
            translations: Dictionary of language codes to translation dictionaries
        """
        self.translations = translations
        self._update_active_translation()

    def set_language(self, lang: str) -> None:
        """
        Set the active language.
        
        Args:
            lang: Language code to set as active
        
        Raises:
            ValueError: If the language is not supported
        """
        if lang not in Settings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {lang}")
        self.lang = lang
        self._update_active_translation()

    def set_model(self, model: str) -> None:
        """
        Set the active AI model.
        
        Args:
            model: Model name to set as active
            
        Raises:
            ValueError: If the model is not supported
        """
        if model not in Settings.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        self.model = model

    def _update_active_translation(self) -> None:
        """Update the active translation based on current language."""
        self.T = self.translations.get(self.lang, self.translations.get("en", {}))
