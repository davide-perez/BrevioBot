from datetime import datetime
import streamlit as st
from typing import Tuple, Optional
from models.state import AppState
from services.tts_service import TextToSpeechService
from config.settings import AppDefaultSettings
import logging

class BrevioBotUI:
    def __init__(self, state: AppState, tts_service: TextToSpeechService):
        self.state = state
        self.tts_service = tts_service
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        if 'input_audio' not in st.session_state:
            st.session_state.input_audio = None
        if 'summary_audio' not in st.session_state:
            st.session_state.summary_audio = None
        if 'summary' not in st.session_state:
            st.session_state.summary = None
        if 'signup_success' not in st.session_state:
            st.session_state.signup_success = False

    def setup_page(self) -> None:
        st.set_page_config(page_title="BrevioBot", layout="centered")
        username = st.session_state.get("username", "User")
        st.title(self.state.T["title"].format(username=username))

    def language_selector(self) -> str:
        return st.selectbox(
            "Lingua / Language",
            AppDefaultSettings.SUPPORTED_LANGUAGES,
            index=AppDefaultSettings.SUPPORTED_LANGUAGES.index(self.state.lang)
        )

    def model_selector(self) -> str:
        return st.selectbox(
            self.state.T["model_label"],
            AppDefaultSettings.SUPPORTED_MODELS,
            index=AppDefaultSettings.SUPPORTED_MODELS.index(self.state.model)
        )

    def text_input_section(self) -> None:
        mode = st.radio(
            self.state.T["input_mode"],
            [self.state.T["upload"], self.state.T["manual"]]
        )
        
        if mode == self.state.T["upload"]:
            uploaded_file = st.file_uploader(
                self.state.T["upload_label"],
                type="txt"
            )
            if uploaded_file:
                self.state.current_text = uploaded_file.read().decode("utf-8")
                self._display_text_tabs("upload_text", self.state.T["upload_label"])
        else:
            self._display_text_tabs("manual_text", self.state.T["text_label"])

    def _display_text_tabs(self, key: str, label: str) -> None:
        tabs = st.tabs(["Text"])
        with tabs[0]:
            self.state.current_text = st.text_area(
                label,
                self.state.current_text,
                height=200,
                key=key
            )

    def summary_section(self) -> None:
        if st.session_state.summary is None:
            return

        summary_audio_key = "summary_audio_data"
        trigger_key = "trigger_summary_audio"

        if st.session_state.get(trigger_key):
            try:
                with st.spinner("Generating audio..."):
                    audio_file = self.tts_service.generate(
                        st.session_state.summary,
                        self.state.lang
                    )
                    with open(audio_file, "rb") as f:
                        st.session_state[summary_audio_key] = f.read()
                    self.tts_service.cleanup_file(audio_file)
            except Exception as e:
                st.error(f"{self.state.T['tts_error']} {str(e)}")
                logging.error("Error during text-to-speech", exc_info=True)
            del st.session_state[trigger_key]
            st.rerun()

        tabs = st.tabs(["Summary", "Audio"])

        with tabs[0]:
            st.text_area(
                self.state.T["result_label"],
                st.session_state.summary,
                height=150,
                key="summary_text"
            )
            if st.checkbox(self.state.T["save_checkbox"]):
                self._handle_download()

        with tabs[1]:
            if st.button(self.state.T["speak_summary"], key="speak_summary"):
                st.session_state[trigger_key] = True
                st.rerun()

            if st.session_state.get(summary_audio_key):
                st.audio(st.session_state[summary_audio_key], format="audio/mp3")

    def _handle_download(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"riassunto_{timestamp}.txt"
        st.download_button(
            label=self.state.T["download"],
            data=st.session_state.summary,
            file_name=filename,
            mime="text/plain"
        )

    def login_screen(self, api_client) -> None:
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'show_signup' not in st.session_state:
            st.session_state.show_signup = False
        if st.session_state.signup_success:
            st.toast(self.state.T["signup_success"])
            st.session_state.signup_success = False
        if st.session_state.show_signup:
            self.signup_screen(api_client)
            st.stop()
        if not st.session_state.logged_in:
            st.title("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                try:
                    success, data = api_client.login(username, password)
                    if success:
                        self.state.set_access_token(data.get("access_token") if data else None)
                        self.state.set_username(username)
                        st.session_state.access_token = data.get("access_token") if data else None
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success(self.state.T["login_success"])
                        st.rerun()
                    else:
                        error_msg = None
                        if data:
                            error_msg = data.get("error")
                        st.toast(error_msg or "Login failed.")
                        logging.error(f"Login error: {error_msg or data}")
                except Exception as e:
                    st.toast(str(e))
                    logging.error(f"Login exception: {str(e)}")
            if st.button("Sign Up"):
                st.session_state.show_signup = True
                st.rerun()
            st.stop()

    def signup_screen(self, api_client) -> None:
        st.title("Sign Up")
        username = st.text_input("Choose a username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        if st.button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match.")
                st.stop()
            try:
                success, data = api_client.signup(username, email, password)
                if success:
                    st.session_state.signup_success = True
                    st.session_state.show_signup = False
                    st.rerun()
                else:
                    error_msg = None
                    if data:
                        error_msg = data.get("error")
                    st.error("Signup failed. " + (error_msg or ""))
                    logging.error(f"Signup error: {error_msg or data}")
            except Exception as e:
                st.error(str(e))
                logging.error(f"Signup exception: {str(e)}")
        if st.button("Back to Login"):
            st.session_state.show_signup = False
            st.rerun()
