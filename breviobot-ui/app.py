import streamlit as st
import logging
from pathlib import Path
from config.settings import AppSettings, AppDefaultSettings
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
    if 'lang' not in st.session_state:
        st.session_state.lang = config.default_lang
    if 'model' not in st.session_state:
        st.session_state.model = config.default_model
    if 'current_text' not in st.session_state:
        st.session_state.current_text = ""
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'translations' not in st.session_state:
        st.session_state.translations = UI
    if 'T' not in st.session_state:
        st.session_state.T = UI.get(st.session_state.lang, UI.get("en", {}))
    api_client = ApiClient(config)
    tts_service = TextToSpeechService(config)
    ui = BrevioBotUI(tts_service)

    ui.login_screen(api_client)
    ui.setup_page()
    lang = ui.language_selector()
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.session_state.T = UI.get(lang, UI.get("en", {}))
    model = ui.model_selector()
    if model != st.session_state.model:
        st.session_state.model = model
    ui.text_input_section()

    if st.button(st.session_state.T["generate"]):
        if st.session_state.current_text.strip():
            try:
                try:
                    new_access_token, new_refresh_token = api_client.auth_service.ensure_valid_access_token()
                except Exception as e:
                    st.toast(f"{st.session_state.T['login_error']} {str(e)}")
                    st.session_state.logged_in = False
                    st.stop()
                with st.spinner(st.session_state.T["spinner"]):
                    logging.info(f"Model used: {st.session_state.model} - Language: {st.session_state.lang}")
                    success, data = api_client.summarize(
                        st.session_state.current_text,
                        st.session_state.model,
                        st.session_state.lang
                    )
                    if success:
                        summary = data.get("summary") if data else None
                        st.session_state.summary = summary
                        st.session_state.summary_audio = None
                        st.success(st.session_state.T["success"])
                    else:
                        error_msg = None
                        if data:
                            error_msg = data.get("error")
                        st.toast(f"{st.session_state.T['error']} {error_msg or 'Summarization failed.'}")
                        logging.error(f"Summarization error: {error_msg or data}")
            except Exception as e:
                st.toast(f"{st.session_state.T['error']} {str(e)}")
                logging.error("Error during summary generation", exc_info=True)

    ui.summary_section()


if __name__ == "__main__":
    main()
