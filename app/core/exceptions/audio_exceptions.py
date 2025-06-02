"""
Исключения для аудио обработки
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any
from .base_exceptions import BaseServiceErrorclass AudioProcessingError(BaseServiceError):
    """
    Ошибка обработки аудио
    
    Используется во всех сервисах аудио обработки:
    - AudioProcessingService
    - AudioConverter
    - AudioProcessor
    - AudioRecognizer
    - AudioStorage
    """
    
    def __init__(
        self, 
        message: str,
        audio_file: Optional[str] = None,
        processing_stage: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            service_name="AudioProcessing",
            message=message,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.audio_file = audio_file
        self.processing_stage = processing_stage
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.audio_file:
            parts.append(f"File: {self.audio_file}")
        
        if self.processing_stage:
            parts.append(f"Stage: {self.processing_stage}")
        
        return " | ".join(parts)class TranscriptionError(AudioProcessingError):
    """
    Ошибка транскрибации аудио
    
    Специализированное исключение для ошибок распознавания речи
    """
    
    def __init__(
        self, 
        message: str,
        audio_file: Optional[str] = None,
        transcription_service: Optional[str] = None,
        audio_duration: Optional[float] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            audio_file=audio_file,
            processing_stage="transcription",
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.transcription_service = transcription_service
        self.audio_duration = audio_duration
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.transcription_service:
            parts.append(f"Service: {self.transcription_service}")
        
        if self.audio_duration:
            parts.append(f"Duration: {self.audio_duration}s")
        
        return " | ".join(parts)class ConversionError(AudioProcessingError):
    """
    Ошибка конвертации аудио
    
    Специализированное исключение для ошибок конвертации форматов
    """
    
    def __init__(
        self, 
        message: str,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        audio_file: Optional[str] = None,
        ffmpeg_error: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            audio_file=audio_file,
            processing_stage="conversion",
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.source_format = source_format
        self.target_format = target_format
        self.ffmpeg_error = ffmpeg_error
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.source_format and self.target_format:
            parts.append(f"Conversion: {self.source_format} → {self.target_format}")
        
        if self.ffmpeg_error:
            parts.append(f"FFmpeg: {self.ffmpeg_error}")
        
        return " | ".join(parts)class AudioValidationError(AudioProcessingError):
    """
    Ошибка валидации аудио файлов
    
    Используется для проверки корректности аудио файлов
    """
    
    def __init__(
        self, 
        message: str,
        audio_file: Optional[str] = None,
        validation_rule: Optional[str] = None,
        expected_value: Any = None,
        actual_value: Any = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            audio_file=audio_file,
            processing_stage="validation",
            error_code=error_code,
            details=details
        )
        self.validation_rule = validation_rule
        self.expected_value = expected_value
        self.actual_value = actual_value
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.validation_rule:
            parts.append(f"Rule: {self.validation_rule}")
        
        if self.expected_value is not None and self.actual_value is not None:
            parts.append(f"Expected: {self.expected_value}, Got: {self.actual_value}")
        
        return " | ".join(parts)
