from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from dataclasses import dataclass
import os
from flask import jsonify, g
from core.exceptions import ValidationError
from core.settings import settings
from auth.auth_service import require_auth
from core.logger import logger
from stt.transcribers import WhisperAPITranscriber, WhisperLocalTranscriber

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
                
        return cls(
            file=file,
            use_api=request_form.get("use_api", str(settings.whisper.use_api)).lower() == 'true',
            model_size=request_form.get("model_size", settings.whisper.model_size)
        )
    
    @staticmethod
    def _allowed_audio_file(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in settings.audio.allowed_formats

@require_auth
def handle_transcribe_request(request_files, request_form):
    request_data = TranscribeRequest.from_request(request_files, request_form)
    
    if request_data.use_api and not settings.is_openai_configured():
        raise ValidationError("OpenAI API key not configured for Whisper API transcription")
    
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing transcription request{user_info} - use_api: {request_data.use_api}, model_size: {request_data.model_size}")
    
    filename = secure_filename(request_data.file.filename)
    temp_path = os.path.join(settings.audio.temp_dir, filename)
    
    os.makedirs(settings.audio.temp_dir, exist_ok=True)
    
    try:
        request_data.file.save(temp_path)
        
        file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        if file_size_mb > settings.audio.max_file_size:
            raise ValidationError(f"File size exceeds maximum limit of {settings.audio.max_file_size}MB")
        
        if request_data.use_api:
            transcriber = WhisperAPITranscriber()
        else:
            transcriber = WhisperLocalTranscriber(request_data.model_size)
        text = transcriber.transcribe(temp_path)
        
        logger.info(f"Successfully transcribed audio{user_info}")
        return jsonify({"text": text})
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)