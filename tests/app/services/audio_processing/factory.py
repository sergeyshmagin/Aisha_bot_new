"""
Фабрика для создания сервисов обработки аудио
"""
from typing import Optional

from app.core.config import settings
from app.services.audio_processing.types import (
    AudioConverter,
    AudioRecognizer,
    AudioProcessor,
    AudioStorage
)
from app.services.audio_processing.converter import PydubAudioConverter
from app.services.audio_processing.recognizer import WhisperRecognizer
from app.services.audio_processing.processor import AudioProcessor
from app.services.audio_processing.storage import LocalAudioStorage
from app.services.audio_processing.service import AudioService

def get_audio_service() -> AudioService:
    """
    Получить сервис обработки аудио с настройками по умолчанию
    
    Returns:
        AudioService: Сервис обработки аудио
    """
    converter, recognizer, processor, storage = AudioServiceFactory.create_all()
    return AudioService(converter, recognizer, processor, storage)

class AudioServiceFactory:
    """Фабрика для создания сервисов обработки аудио"""
    
    @staticmethod
    def create_converter(ffmpeg_path: Optional[str] = None) -> AudioConverter:
        """
        Создает конвертер аудио
        
        Args:
            ffmpeg_path: Путь к ffmpeg
            
        Returns:
            AudioConverter: Конвертер аудио
        """
        return PydubAudioConverter(ffmpeg_path)
    
    @staticmethod
    def create_recognizer(api_key: Optional[str] = None) -> AudioRecognizer:
        """
        Создает распознаватель речи
        
        Args:
            api_key: API ключ OpenAI
            
        Returns:
            AudioRecognizer: Распознаватель речи
        """
        return WhisperRecognizer(api_key)
    
    @staticmethod
    def create_processor(ffmpeg_path: Optional[str] = None) -> AudioProcessor:
        """
        Создает процессор аудио
        
        Args:
            ffmpeg_path: Путь к ffmpeg
            
        Returns:
            AudioProcessor: Процессор аудио
        """
        return AudioProcessor(ffmpeg_path)
    
    @staticmethod
    def create_storage(storage_path: Optional[str] = None) -> AudioStorage:
        """
        Создает хранилище аудио
        
        Args:
            storage_path: Путь к директории хранения
            
        Returns:
            AudioStorage: Хранилище аудио
        """
        return LocalAudioStorage(storage_path)
    
    @classmethod
    def create_all(cls) -> tuple[AudioConverter, AudioRecognizer, AudioProcessor, AudioStorage]:
        """
        Создает все сервисы с настройками по умолчанию
        
        Returns:
            tuple: Кортеж из всех сервисов
        """
        return (
            cls.create_converter(),
            cls.create_recognizer(),
            cls.create_processor(),
            cls.create_storage()
        ) 