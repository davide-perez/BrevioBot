import streamlit as st
import logging
from pathlib import Path
from config.settings import AppSettings, AppDefaultSettings
from models.state import AppState
from ui.components import BrevioBotUI
from services.api_client import ApiClient
from services.tts_service import TextToSpeechService
from translations import UI


def setup_logging() -> None:
    log_dir = AppDefaultSettings.LOG_DIR
    log_dir.mkdir(exist_ok=True)
    log_level = getattr(logging, AppSettings.load().log_level.upper(), logging.ERROR)
    logging.basicConfig(
        filename=log_dir / "breviobot.log",
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main() -> None:
    setup_logging()
    config = AppSettings.load()
    state = AppState(config)
    state.set_translations(UI)
    api_client = ApiClient(config)
    tts_service = TextToSpeechService(config)
    ui = BrevioBotUI(state, tts_service)
    ui.setup_page()
    lang = ui.language_selector()
    if lang != state.lang:
        state.set_language(lang)
    model = ui.model_selector()
    if model != state.model:
        state.set_model(model)
    ui.text_input_section()

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

    ui.summary_section()


if __name__ == "__main__":
    main()
