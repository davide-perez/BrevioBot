import streamlit as st
from datetime import datetime
from state import AppState
from config import Config
from tts import TextToSpeech
import logging

class BrevioBotUI:
    def __init__(self, state: AppState):
        self.state = state

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
            self._handle_file_upload()
        else:
            self._handle_manual_input()

    def _handle_file_upload(self):
        uploaded_file = st.file_uploader(self.state.T["upload_label"], type="txt")
        if uploaded_file:
            self.state.current_text = uploaded_file.read().decode("utf-8")
            self._display_text_area("upload_text", self.state.T["upload_label"])

    def _handle_manual_input(self):
        self._display_text_area("manual_text", self.state.T["text_label"])

    def _display_text_area(self, key: str, label: str):
        col1, col2 = st.columns([4, 1])
        with col1:
            self.state.current_text = st.text_area(label, self.state.current_text, height=200, key=key)
        with col2:
            if st.button(self.state.T["speak_input"], key=f"speak_input_{key}"):
                self._generate_audio(self.state.current_text, "input")
            if self.state.input_audio is not None:
                st.audio(self.state.input_audio, format="audio/mp3")

    def summary_section(self):
        if self.state.summary is not None:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_area(self.state.T["result_label"], self.state.summary, height=150, key="summary_text")
            with col2:
                if st.button(self.state.T["speak_summary"], key="speak_summary"):
                    self._generate_audio(self.state.summary, "summary")
                if self.state.summary_audio is not None:
                    st.audio(self.state.summary_audio, format="audio/mp3")

            if st.checkbox(self.state.T["save_checkbox"]):
                self._handle_download()

    def _handle_download(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"riassunto_{timestamp}.txt"
        st.download_button(
            label=self.state.T["download"],
            data=self.state.summary,
            file_name=filename,
            mime="text/plain"
        )

    def _generate_audio(self, text: str, key_prefix: str):
        try:
            audio_file = TextToSpeech.generate(text, self.state.lang)
            with open(audio_file, "rb") as f:
                if key_prefix == "input":
                    self.state.input_audio = f.read()
                else:
                    self.state.summary_audio = f.read()
            TextToSpeech.cleanup_file(audio_file)
        except Exception as e:
            st.error(f"{self.state.T['tts_error']} {str(e)}")
            logging.error("Error during text-to-speech", exc_info=True)
