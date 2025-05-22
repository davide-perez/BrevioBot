import streamlit as st
from summarizer import summarize_text
from speech import text_to_speech
from datetime import datetime
import logging
import os
import tempfile
from dotenv import load_dotenv
from translations import UI

load_dotenv()

def generate_audio(text, lang, key_prefix):
    try:
        audio_file = text_to_speech(text, lang)
        with open(audio_file, "rb") as f:
            st.session_state[f"{key_prefix}_audio"] = f.read()
        os.unlink(audio_file)
    except Exception as e:
        st.error(f"{st.session_state.T['tts_error']} {str(e)}")
        logging.error("Error during text-to-speech", exc_info=True)

def on_speak_input():
    if st.session_state.current_text:
        generate_audio(st.session_state.current_text, st.session_state.lang, "input")

def on_speak_summary():
    if st.session_state.summary:
        generate_audio(st.session_state.summary, st.session_state.lang, "summary")

def on_generate():
    if st.session_state.current_text.strip():
        try:
            with st.spinner(st.session_state.T["spinner"]):
                logging.info(f"Modello usato: {st.session_state.model} - Lingua: {st.session_state.lang}")
                st.session_state.summary = summarize_text(st.session_state.current_text, st.session_state.model, st.session_state.lang)
                st.session_state.summary_audio = None
            st.success(st.session_state.T["success"])
        except Exception as e:
            st.toast(f"{st.session_state.T['error']} {str(e)}")
            logging.error("Error during summary generation", exc_info=True)

if "input_audio" not in st.session_state:
    st.session_state.input_audio = None
if "summary_audio" not in st.session_state:
    st.session_state.summary_audio = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "current_text" not in st.session_state:
    st.session_state.current_text = ""

st.set_page_config(page_title="BrevioBot", layout="centered")
default_lang = os.environ.get("DEFAULT_LANG", "it")
lang = st.selectbox("Lingua / Language", ["it", "en"], index=0 if default_lang == "it" else 1)
T = UI[lang]
st.session_state.T = T
st.session_state.lang = lang

st.title(T["title"])

logging.basicConfig(
    filename="log/breviobot.log",
    level=os.environ.get("LOG_LEVEL", "ERROR"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

model = st.selectbox(
    T["model_label"],
    ["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"],
    index=["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"].index(
        os.environ.get("DEFAULT_MODEL", "llama3"))
)
st.session_state.model = model

mode = st.radio(T["input_mode"], [T["upload"], T["manual"]])

if mode == T["upload"]:
    uploaded_file = st.file_uploader(T["upload_label"], type="txt")
    if uploaded_file:
        st.session_state.current_text = uploaded_file.read().decode("utf-8")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text_area(T["upload_label"], st.session_state.current_text, height=200, key="upload_text")
        with col2:
            st.button(T["speak_input"], key="speak_input_upload", on_click=on_speak_input)
            if st.session_state.input_audio is not None:
                st.audio(st.session_state.input_audio, format="audio/mp3")
elif mode == T["manual"]:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.session_state.current_text = st.text_area(T["text_label"], height=200, key="manual_text")
    with col2:
        st.button(T["speak_input"], key="speak_input_manual", on_click=on_speak_input)
        if st.session_state.input_audio is not None:
            st.audio(st.session_state.input_audio, format="audio/mp3")

save_to_file = st.checkbox(T["save_checkbox"])

st.button(T["generate"], on_click=on_generate)

if st.session_state.summary is not None:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.text_area(T["result_label"], st.session_state.summary, height=150, key="summary_text")
    with col2:
        st.button(T["speak_summary"], key="speak_summary", on_click=on_speak_summary)
        if st.session_state.summary_audio is not None:
            st.audio(st.session_state.summary_audio, format="audio/mp3")

    if save_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"riassunto_{timestamp}.txt"
        st.download_button(
            label=T["download"],
            data=st.session_state.summary,
            file_name=filename,
            mime="text/plain"
        )
