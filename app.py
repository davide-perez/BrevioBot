import streamlit as st
from summarizer import summarize_text
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from translations import UI

load_dotenv()

st.set_page_config(page_title="BrevioBot", layout="centered")
default_lang = os.environ.get("DEFAULT_LANG", "it")
lang = st.selectbox("Lingua / Language", ["it", "en"], index=0 if default_lang == "it" else 1)
T = UI[lang]

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

mode = st.radio(T["input_mode"], [T["upload"], T["manual"]])
content = ""

if mode == T["upload"]:
    uploaded_file = st.file_uploader(T["upload_label"], type="txt")
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.text_area(T["upload_label"], content, height=200)
elif mode == T["manual"]:
    content = st.text_area(T["text_label"], height=200)

save_to_file = st.checkbox(T["save_checkbox"])

if content.strip() and st.button(T["generate"]):
    try:
        with st.spinner(T["spinner"]):
            logging.info(f"Modello usato: {model} - Lingua: {lang}")
            summary = summarize_text(content, model, lang)

        st.success(T["success"])
        st.text_area(T["result_label"], summary, height=150)

        if save_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"riassunto_{timestamp}.txt"
            st.toast(T["download_ready"])
            st.download_button(
                label=T["download"],
                data=summary,
                file_name=filename,
                mime="text/plain"
            )

    except Exception as e:
        st.toast(f"{T['error']} {str(e)}")
        logging.error("Errore durante il riassunto", exc_info=True)
