import streamlit as st
from datetime import datetime
from state import AppState
from config import Config
from tts import TextToSpeech
import logging

class BrevioBotUI:
    def __init__(self, state: AppState):
        self.state = state
        if 'input_audio' not in st.session_state:
            st.session_state.input_audio = None
        if 'summary_audio' not in st.session_state:
            st.session_state.summary_audio = None
        if 'summary' not in st.session_state:
            st.session_state.summary = None

    def setup_page(self):
        st.set_page_config(page_title="BrevioBot", layout="centered")
        st.title(self.state.T["title"])

    def language_selector(self):
        lang = st.selectbox(
            "Lingua / Language",
            self.state.config.SUPPORTED_LANGUAGES,
            index=self.state.config.SUPPORTED_LANGUAGES.index(self.state.lang)
        )
        return lang

    def model_selector(self):
        return st.selectbox(
            self.state.T["model_label"],
            self.state.config.SUPPORTED_MODELS,
            index=self.state.config.SUPPORTED_MODELS.index(self.state.model)
        )

    def text_input_section(self):
        mode = st.radio(self.state.T["input_mode"], [self.state.T["upload"], self.state.T["manual"]])
        
        if mode == self.state.T["upload"]:
            uploaded_file = st.file_uploader(self.state.T["upload_label"], type="txt")
            if uploaded_file:
                self.state.current_text = uploaded_file.read().decode("utf-8")
                self._display_text_tabs("upload_text", self.state.T["upload_label"])
        else:
            self._display_text_tabs("manual_text", self.state.T["text_label"])


    def _display_text_tabs(self, key: str, label: str):
        input_audio_key = f"input_audio_{key}"
        trigger_key = f"trigger_audio_{key}"

        # 1. TTS generation happens before rendering tabs
        if st.session_state.get(trigger_key):
            try:
                with st.spinner("Generating audio..."):
                    audio_file = TextToSpeech.generate(self.state.current_text, self.state.lang)
                    with open(audio_file, "rb") as f:
                        st.session_state[input_audio_key] = f.read()
                    TextToSpeech.cleanup_file(audio_file)
            except Exception as e:
                st.error(f"{self.state.T['tts_error']} {str(e)}")
                logging.error("Error during text-to-speech", exc_info=True)
            del st.session_state[trigger_key]
            st.rerun()  # force immediate clean rerender

        # 2. Now render tabs with no side effects
        tabs = st.tabs(["Text", "Audio"])

        with tabs[0]:
            self.state.current_text = st.text_area(label, self.state.current_text, height=200, key=key)

        with tabs[1]:
            if st.button(self.state.T["speak_input"], key=f"speak_input_{key}"):
                st.session_state[trigger_key] = True
                st.rerun()

            if st.session_state.get(input_audio_key):
                st.audio(st.session_state[input_audio_key], format="audio/mp3")



    def summary_section(self):
        if st.session_state.summary is None:
            return

        summary_audio_key = "summary_audio_data"
        trigger_key = "trigger_summary_audio"

        # Handle TTS trigger before rendering tabs (prevents UI duplication)
        if st.session_state.get(trigger_key):
            try:
                with st.spinner("Generating audio..."):
                    audio_file = TextToSpeech.generate(st.session_state.summary, self.state.lang)
                    with open(audio_file, "rb") as f:
                        st.session_state[summary_audio_key] = f.read()
                    TextToSpeech.cleanup_file(audio_file)
            except Exception as e:
                st.error(f"{self.state.T['tts_error']} {str(e)}")
                logging.error("Error during text-to-speech", exc_info=True)
            del st.session_state[trigger_key]
            st.rerun()

        tabs = st.tabs(["Summary", "Audio"])

        with tabs[0]:
            st.text_area(self.state.T["result_label"], st.session_state.summary, height=150, key="summary_text")
            if st.checkbox(self.state.T["save_checkbox"]):
                self._handle_download()

        with tabs[1]:
            if st.button(self.state.T["speak_summary"], key="speak_summary"):
                st.session_state[trigger_key] = True
                st.rerun()

            if st.session_state.get(summary_audio_key):
                st.audio(st.session_state[summary_audio_key], format="audio/mp3")



    def _handle_download(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"riassunto_{timestamp}.txt"
        st.download_button(
            label=self.state.T["download"],
            data=st.session_state.summary,
            file_name=filename,
            mime="text/plain"
        )
