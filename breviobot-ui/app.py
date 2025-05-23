import streamlit as st
import logging
import os

# Import UI components locally
from state import AppState
from ui_components import BrevioBotUI
from translations import UI
from api_client import ApiClient

# Initialize configuration
SUPPORTED_LANGUAGES = ["it", "en"]
SUPPORTED_MODELS = ["llama3", "llama3:instruct", "mistral", "gpt-3.5-turbo", "gpt-4"]
DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "it")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama3")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "ERROR")

# Initialize configuration and state
config = type("Config", (), {
    "SUPPORTED_LANGUAGES": SUPPORTED_LANGUAGES,
    "SUPPORTED_MODELS": SUPPORTED_MODELS,
    "DEFAULT_LANG": DEFAULT_LANG,
    "DEFAULT_MODEL": DEFAULT_MODEL,
    "LOG_LEVEL": LOG_LEVEL
})()

state = AppState(config)

# Initialize components
ui = BrevioBotUI(state)
api_client = ApiClient()

# Setup logging directory
log_dir = os.path.join(os.path.dirname(__file__), "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Setup logging
logging.basicConfig(
    filename=os.path.join(log_dir, "breviobot.log"),
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    # Setup UI
    ui.setup_page()
    
    # Language selection
    lang = ui.language_selector()
    if lang != state.lang:
        state.set_language(lang, UI)
    
    # Model selection
    model = ui.model_selector()
    if model != state.model:
        state.set_model(model)
    
    # Text input
    ui.text_input_section()
      # Generate summary button    
    if st.button(state.T["generate"]):
        if state.current_text.strip():
            try:
                with st.spinner(state.T["spinner"]):
                    logging.info(f"Model used: {state.model} - Language: {state.lang}")
                    state.summary = api_client.summarize(
                        state.current_text, state.lang
                    )
                    state.summary_audio = None
                st.success(state.T["success"])
            except Exception as e:
                st.toast(f"{state.T['error']} {str(e)}")
                logging.error("Error during summary generation", exc_info=True)
    
    # Display summary and audio controls
    ui.summary_section()

if __name__ == "__main__":
    main()
