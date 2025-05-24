import streamlit as st
import logging
from pathlib import Path
from src.config.settings import Config, Settings
from src.models.state import AppState
from src.ui.components import BrevioBotUI
from src.services.api_client import ApiClient
from src.services.tts_service import TextToSpeechService
from translations import UI


def setup_logging() -> None:
    """Configure the application logging."""
    log_dir = Settings.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        filename=log_dir / "breviobot.log",
        level=Settings.LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def main() -> None:
    """Main application entry point."""
    setup_logging()
    
    # Initialize services and state
    config = Config.load()
    state = AppState(config)
    state.set_translations(UI)
    
    api_client = ApiClient(config)
    tts_service = TextToSpeechService(config)
    ui = BrevioBotUI(state, tts_service)

    # Setup UI
    ui.setup_page()
    
    # Handle language selection
    lang = ui.language_selector()
    if lang != state.lang:
        state.set_language(lang)
        
    # Handle model selection
    model = ui.model_selector()
    if model != state.model:
        state.set_model(model)
        
    # Display text input section
    ui.text_input_section()
    
    # Handle summarization
    if st.button(state.T["generate"]):
        if state.current_text.strip():
            try:
                with st.spinner(state.T["spinner"]):
                    logging.info(f"Model used: {state.model} - Language: {state.lang}")
                    summary = api_client.summarize(
                        state.current_text,
                        state.model,
                        state.lang
                    )
                    state.summary = summary
                    st.session_state.summary = summary
                    st.session_state.summary_audio = None
                st.success(state.T["success"])
            except Exception as e:
                st.toast(f"{state.T['error']} {str(e)}")
                logging.error("Error during summary generation", exc_info=True)
                
    # Display summary section
    ui.summary_section()

if __name__ == "__main__":
    main()
