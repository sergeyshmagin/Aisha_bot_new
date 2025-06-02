"""
Модульная структура исключений
Рефакторинг app/core/exceptions.py (598 строк → модули)
"""

# Базовые исключения
from .base_exceptions import (
    BaseAppError,
    BaseServiceError,
    BaseValidationError,
    BaseConfigurationError
)

# Исключения аудио обработки
from .audio_exceptions import (
    AudioProcessingError,
    TranscriptionError,
    ConversionError
)

# Исключения хранения и сети
from .storage_exceptions import (
    StorageError,
    NetworkError,
    TimeoutError
)

# Исключения валидации
from .validation_exceptions import (
    ValidationError,
    InvalidFormatError,
    InvalidParameterError,
    InvalidStateError
)

# Исключения конфигурации
from .config_exceptions import (
    ConfigurationError,
    DependencyError,
    InvalidCredentialsError
)

# Исключения аватаров (если понадобятся)
from .avatar_exceptions import (
    AvatarError,
    AvatarTrainingError,
    AvatarValidationError
)

__all__ = [
    # Базовые
    "BaseAppError",
    "BaseServiceError", 
    "BaseValidationError",
    "BaseConfigurationError",
    
    # Аудио
    "AudioProcessingError",
    "TranscriptionError",
    "ConversionError",
    
    # Хранение и сеть
    "StorageError",
    "NetworkError",
    "TimeoutError",
    
    # Валидация
    "ValidationError",
    "InvalidFormatError",
    "InvalidParameterError",
    "InvalidStateError",
    
    # Конфигурация
    "ConfigurationError",
    "DependencyError",
    "InvalidCredentialsError",
    
    # Аватары
    "AvatarError",
    "AvatarTrainingError",
    "AvatarValidationError"
]
