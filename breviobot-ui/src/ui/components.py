from datetime import datetime
import streamlit as st
from typing import Tuple, Optional
from ..models.state import AppState
from ..services.tts_service import TextToSpeechService
from ..config.settings import Settings
import logging

class BrevioBotUI:
    """Main UI component class for the BrevioBot application."""
    
    def __init__(self, state: AppState, tts_service: TextToSpeechService):
        """
        Initialize the UI components.
        
        Args:
            state: Application state instance
            tts_service: Text-to-speech service instance
        """
        self.state = state
        self.tts_service = tts_service
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if 'input_audio' not in st.session_state:
            st.session_state.input_audio = None
        if 'summary_audio' not in st.session_state:
            st.session_state.summary_audio = None
        if 'summary' not in st.session_state:
            st.session_state.summary = None

    def setup_page(self) -> None:
        """Configure the page layout and title."""
        st.set_page_config(page_title="BrevioBot", layout="centered")
        st.title(self.state.T["title"])

    def language_selector(self) -> str:
        """
        Render the language selection widget.
        
        Returns:
            str: Selected language code
        """
        return st.selectbox(
            "Lingua / Language",
            Settings.SUPPORTED_LANGUAGES,
            index=Settings.SUPPORTED_LANGUAGES.index(self.state.lang)
        )

    def model_selector(self) -> str:
        """
        Render the model selection widget.
        
        Returns:
            str: Selected model name
        """
        return st.selectbox(
            self.state.T["model_label"],
            Settings.SUPPORTED_MODELS,
            index=Settings.SUPPORTED_MODELS.index(self.state.model)
        )

    def text_input_section(self) -> None:
        """Render the text input section with file upload and manual input options."""
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
        """
        Display text input tabs.
        
        Args:
            key: Unique key for the text area
            label: Label for the text area
        """
        tabs = st.tabs(["Text"])
        with tabs[0]:
            self.state.current_text = st.text_area(
                label,
                self.state.current_text,
                height=200,
                key=key
            )

    def summary_section(self) -> None:
        """Render the summary section with text and audio options."""
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
        """Handle the download of the summary text."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"riassunto_{timestamp}.txt"
        st.download_button(
            label=self.state.T["download"],
            data=st.session_state.summary,
            file_name=filename,
            mime="text/plain"
        )
