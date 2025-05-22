import streamlit as st
import logging
from breviobot.core.config import Config
from breviobot.models.state import AppState
from breviobot.core.summarizer import TextSummarizer
from breviobot.ui.ui_components import BrevioBotUI
from breviobot.utils.translations import UI
from breviobot.utils.prompts import PROMPTS

# Initialize configuration and state
config = Config.load()
state = AppState(config)

# Initialize components
ui = BrevioBotUI(state)
summarizer = TextSummarizer(config, PROMPTS, UI)

# Setup logging
logging.basicConfig(
    filename="log/breviobot.log",
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
                    state.summary = summarizer.summarize_text(
                        state.current_text, state.model, state.lang
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
