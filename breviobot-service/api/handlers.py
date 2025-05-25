from flask import jsonify
from dataclasses import dataclass
from typing import Optional
from werkzeug.datastructures import FileStorage

from text.summary_service import TextSummarizer
from core.prompts import PROMPTS
from core.settings import settings
from core.logger import logger
from core.exceptions import BrevioBotError, ValidationError, RateLimitError, ConfigurationError

@dataclass
class SummarizeRequest:
    text: str
    language: str
    model: str

    @classmethod
    def from_json(cls, data: dict) -> 'SummarizeRequest':
        if not data.get("text"):
            raise ValidationError("Text field is required")
        
        if len(data["text"]) > settings.app.max_input_length:
            raise ValidationError(f"Text exceeds maximum length of {settings.app.max_input_length}")
        
        return cls(
            text=data["text"],
            language=data.get("language", settings.app.default_language),
            model=data.get("model", settings.app.default_model)
        )

@dataclass
class TranscribeRequest:
    file: FileStorage
    use_api: bool
    model_size: str

    @classmethod
    def from_request(cls, request_files, request_form) -> 'TranscribeRequest':
        if 'file' not in request_files:
            raise ValidationError("No audio file provided")
            
        file = request_files['file']
        if file.filename == '':
            raise ValidationError("No selected file")
            
        if not cls._allowed_audio_file(file.filename):
            allowed_formats = ", ".join(settings.audio.allowed_formats)
            raise ValidationError(f"File type not allowed. Supported formats: {allowed_formats}")
        
        # Check file size (FileStorage doesn't provide size directly, so we'll check during save)
        
        return cls(
            file=file,
            use_api=request_form.get("use_api", str(settings.whisper.use_api)).lower() == 'true',
            model_size=request_form.get("model_size", settings.whisper.model_size)
        )
    
    @staticmethod
    def _allowed_audio_file(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in settings.audio.allowed_formats

def handle_breviobot_error(error):
    logger.error(f"Unhandled BrevioBotError: {str(error)}", exc_info=True)
    return jsonify({"error": str(error)}), 500

def handle_general_error(error):
    logger.error(f"Unhandled unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred. Please check the logs for details."}), 500

def handle_summarize_request(request_json):
    # Validate OpenAI configuration for GPT models
    request_data = SummarizeRequest.from_json(request_json or {})
    
    if request_data.model.startswith("gpt") and not settings.is_openai_configured():
        raise ConfigurationError("OpenAI API key not configured for GPT models")
    
    logger.info(f"Processing summarization request for language: {request_data.language}, model: {request_data.model}")
    
    summarizer = TextSummarizer(settings.app.openai_api_key, PROMPTS)
    result = summarizer.summarize_text(
        request_data.text,
        request_data.model,
        request_data.language
    )
    
    logger.info("Successfully generated summary")
    return jsonify({"summary": result})

def handle_transcribe_request(request_files, request_form):
    import os
    from werkzeug.utils import secure_filename
    from stt.transcription_services import WhisperAPITranscriber, WhisperLocalTranscriber
    
    request_data = TranscribeRequest.from_request(request_files, request_form)
    
    # Validate OpenAI configuration for API transcription
    if request_data.use_api and not settings.is_openai_configured():
        raise ConfigurationError("OpenAI API key not configured for Whisper API transcription")
    
    logger.info(f"Processing transcription request - use_api: {request_data.use_api}, model_size: {request_data.model_size}")
    
    filename = secure_filename(request_data.file.filename)
    temp_path = os.path.join(settings.audio.temp_dir, filename)
    
    os.makedirs(settings.audio.temp_dir, exist_ok=True)
    
    try:
        # Save the file temporarily
        request_data.file.save(temp_path)
        
        # Check file size after saving
        file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        if file_size_mb > settings.audio.max_file_size:
            raise ValidationError(f"File size exceeds maximum limit of {settings.audio.max_file_size}MB")
        
        # Create appropriate transcriber
        if request_data.use_api:
            transcriber = WhisperAPITranscriber()
        else:
            transcriber = WhisperLocalTranscriber(request_data.model_size)
        
        # Transcribe the audio
        text = transcriber.transcribe(temp_path)
        
        logger.info("Successfully transcribed audio")
        return jsonify({"text": text})
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
