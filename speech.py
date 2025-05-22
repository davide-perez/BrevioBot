import tempfile
from gtts import gTTS

def text_to_speech(text, lang_code):
    """Convert text to speech using Google Text-to-Speech.
    
    Args:
        text (str): The text to convert to speech
        lang_code (str): Language code (it/en)
    
    Returns:
        str: Path to the temporary audio file
    """
    # Map our language codes to gTTS language codes
    lang_map = {
        "it": "it",
        "en": "en"
    }
    tts_lang = lang_map.get(lang_code, "en")
    
    # Create a temporary file for the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        tts = gTTS(text=text, lang=tts_lang)
        tts.save(temp_file.name)
        return temp_file.name
