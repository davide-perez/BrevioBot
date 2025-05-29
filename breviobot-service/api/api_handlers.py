from flask import jsonify, g
from dataclasses import dataclass
from typing import Optional
from werkzeug.datastructures import FileStorage

from text.summary_service import TextSummarizer
from core.prompts import PROMPTS
from core.settings import settings
from core.logger import logger
from core.exceptions import ValidationError, AuthenticationError
from auth.auth_service import require_auth, AuthService
from sqlalchemy.exc import IntegrityError
import re
from core.email_utils import send_email
import secrets
import os
from werkzeug.utils import secure_filename
from stt.transcription_services import WhisperAPITranscriber, WhisperLocalTranscriber
from core.users import User
from persistence.user_repository import UserRepository
from persistence.db_session import SessionLocal

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
                
        return cls(
            file=file,
            use_api=request_form.get("use_api", str(settings.whisper.use_api)).lower() == 'true',
            model_size=request_form.get("model_size", settings.whisper.model_size)
        )
    
    @staticmethod
    def _allowed_audio_file(filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in settings.audio.allowed_formats


def handle_general_error(error):
    logger.error(f"Unhandled unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred. Please check the service logs for details."}), 500

def handle_authentication_error(error):
    logger.warning(f"Authentication error: {str(error)}")
    return jsonify({"error": str(error)}), 401

def handle_validation_error(error):
    logger.error(f"Validation error: {str(error)}")
    return jsonify({"error": str(error)}), 400

@require_auth
def handle_summarize_request(request_json):
    request_data = SummarizeRequest.from_json(request_json or {})
    
    if request_data.model.startswith("gpt") and not settings.is_openai_configured():
        raise Exception("OpenAI API key not configured for GPT models")
    user_info = f" for user: {g.current_user['username']}" if hasattr(g, 'current_user') else ""
    logger.info(f"Processing summarization request{user_info} for language: {request_data.language}, model: {request_data.model}")
    
    summarizer = TextSummarizer(settings.app.openai_api_key, PROMPTS)
    result = summarizer.summarize_text(
        request_data.text,
        request_data.model,
        request_data.language
    )
    
    logger.info(f"Successfully generated summary{user_info}")
    return jsonify({"summary": result})

@require_auth
def handle_transcribe_request(request_files, request_form):
    request_data = TranscribeRequest.from_request(request_files, request_form)
    
    if request_data.use_api and not settings.is_openai_configured():
        raise Exception("OpenAI API key not configured for Whisper API transcription")
    
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

def handle_create_user_request(user_data):
    if not user_data.get("username") or not user_data.get("email"):
        raise ValidationError("Username and email are required fields")
    if not user_data.get("password"):
        raise ValidationError("Password is required")

    db = SessionLocal()
    repo = UserRepository(lambda: db)

    existing_user = repo.get_by_username(user_data["username"])
    if existing_user:
        db.close()
        raise ValidationError(f"User with username '{user_data['username']}' already exists")

    verification_token = secrets.token_urlsafe(32)

    user = User(
        id=0,
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data.get("full_name"),
        is_active=True,
        is_admin=user_data.get("is_admin", False),
        password=user_data["password"]
    )

    try:
        db_user = repo.create(user, is_verified=False, verification_token=verification_token)
        verify_url = f"http://localhost:8000/api/auth/verify?token={verification_token}"
        email_body = f"""
        <p>Welcome to BrevioBot!</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href='{verify_url}'>Verify Email</a></p>
        <p>If you did not register, please ignore this email.</p>
        """
        send_email(db_user.email, "Verify your email for BrevioBot", email_body)
        user_dict = User.model_validate(db_user).model_dump()
        return {
            "username": user_dict["username"],
            "email": user_dict["email"],
            "role": "admin" if user_dict.get("is_admin") else "user",
            "message": "Registration successful. Please check your email to verify your account."
        }
    except IntegrityError as e:
        db.rollback()
        import re
        msg = str(e.orig).lower()
        match = re.search(r'unique constraint failed: [\w]+\.([a-z_]+)', msg)
        if match:
            field = match.group(1)
            raise ValidationError(f"A user with this {field} already exists")
        else:
            raise ValidationError("A user with the provided information already exists")
    finally:
        db.close()

def handle_login_request(login_data):
    username = login_data.get("username")
    password = login_data.get("password")
    if not username or not password:
        raise AuthenticationError("Username and password are required")

    auth_service = AuthService()
    user_info = auth_service.authenticate_user(username, password)

    from persistence.user_repository import UserRepository
    from persistence.db_session import SessionLocal
    with SessionLocal() as db:
        repo = UserRepository(lambda: db)
        user_db = repo.get_by_username(username)
        if not user_db.is_verified:
            raise AuthenticationError("Email not verified. Please check your email for the verification link.")

    access_token = auth_service.generate_token({
        "user_id": user_info["user_id"],
        "username": user_info["username"]
    })
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user_info["username"],
            "email": user_info.get("email"),
            "role": user_info["role"]
        }
    }