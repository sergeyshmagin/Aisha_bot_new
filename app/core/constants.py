"""
Константы приложения
"""
from enum import Enum
from typing import Final

# Импортируем настройки для констант стоимости
from app.core.config import settings

# Названия директорий
STORAGE_DIR: Final[str] = "storage"
AUDIO_DIR: Final[str] = "audio"
TEMP_DIR: Final[str] = "temp"

# Расширения файлов
MP3_EXTENSION: Final[str] = ".mp3"
WAV_EXTENSION: Final[str] = ".wav"
OGG_EXTENSION: Final[str] = ".ogg"
M4A_EXTENSION: Final[str] = ".m4a"

# Кодеки
MP3_CODEC: Final[str] = "libmp3lame"
WAV_CODEC: Final[str] = "pcm_s16le"
OGG_CODEC: Final[str] = "libvorbis"
M4A_CODEC: Final[str] = "aac"

# Частота дискретизации
DEFAULT_SAMPLE_RATE: Final[int] = 44100

# Каналы
MONO: Final[int] = 1
STEREO: Final[int] = 2

# Битрейт
DEFAULT_BITRATE: Final[str] = "192k"

# Языки
class Language(str, Enum):
    """Поддерживаемые языки"""
    RUSSIAN = "ru"
    ENGLISH = "en"

# Статусы обработки
class ProcessingStatus(str, Enum):
    """Статусы обработки аудио"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Ошибки
class ErrorCode(str, Enum):
    """Коды ошибок"""
    INVALID_FILE = "invalid_file"
    INVALID_FORMAT = "invalid_format"
    FILE_TOO_LARGE = "file_too_large"
    CONVERSION_FAILED = "conversion_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    STORAGE_ERROR = "storage_error"
    UNKNOWN_ERROR = "unknown_error"

# Метрики
class MetricName(str, Enum):
    """Названия метрик"""
    AUDIO_PROCESSING_TIME = "audio_processing_time"
    AUDIO_CONVERSION_TIME = "audio_conversion_time"
    AUDIO_TRANSCRIPTION_TIME = "audio_transcription_time"
    AUDIO_FILE_SIZE = "audio_file_size"
    AUDIO_DURATION = "audio_duration"
    ERROR_COUNT = "error_count"
    SUCCESS_COUNT = "success_count"

# Алерты
class AlertLevel(str, Enum):
    """Уровни алертов"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Логирование
class LogLevel(str, Enum):
    """Уровни логирования"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# Лимиты
MAX_AVATAR_NAME_LENGTH = 50
MIN_AVATAR_NAME_LENGTH = 2

# Лимиты для транскрибации
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 МБ
MAX_AUDIO_DURATION = 60 * 60  # 60 минут
MAX_TRANSCRIPTS_PER_USER = 50

# Таймауты
TRAINING_CHECK_INTERVAL = 60  # секунды
TRAINING_MAX_DURATION = 3600  # 1 час

# Размеры файлов
# MAX_PHOTO_SIZE = 5 * 1024 * 1024  # УДАЛЕНО: заменено на PHOTO_MAX_SIZE из settings
# MIN_PHOTO_DIMENSION = 512  # УДАЛЕНО: заменено на PHOTO_MIN_RESOLUTION из settings  
# MAX_PHOTO_DIMENSION = 4096  # УДАЛЕНО: заменено на PHOTO_MAX_RESOLUTION из settings

# Форматы файлов
# ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png"}  # УДАЛЕНО: см. PHOTO_ALLOWED_FORMATS
# ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png"}  # УДАЛЕНО: см. PHOTO_ALLOWED_FORMATS

# =============================================================================
# СТОИМОСТЬ ГЕНЕРАЦИИ (импортируем из настроек)
# =============================================================================

# Генерация изображений с аватаром (FLUX)
GENERATION_COST: Final[float] = settings.IMAGE_GENERATION_COST

# Создание аватара
AVATAR_CREATION_COST: Final[float] = settings.AVATAR_CREATION_COST

# Imagen 4 генерация
IMAGEN4_GENERATION_COST: Final[float] = settings.IMAGEN4_GENERATION_COST

# Транскрибация
TRANSCRIPTION_COST_PER_MINUTE: Final[float] = settings.TRANSCRIPTION_COST_PER_MINUTE

# Видео генерация
VIDEO_5S_GENERATION_COST: Final[float] = settings.VIDEO_5S_GENERATION_COST
VIDEO_10S_GENERATION_COST: Final[float] = settings.VIDEO_10S_GENERATION_COST
VIDEO_PRO_5S_GENERATION_COST: Final[float] = settings.VIDEO_PRO_5S_GENERATION_COST
VIDEO_PRO_10S_GENERATION_COST: Final[float] = settings.VIDEO_PRO_10S_GENERATION_COST
PORN_VIDEO_5S_GENERATION_COST: Final[float] = settings.PORN_VIDEO_5S_GENERATION_COST
PORN_VIDEO_10S_GENERATION_COST: Final[float] = settings.PORN_VIDEO_10S_GENERATION_COST

# =============================================================================
# ЛИМИТЫ АВАТАРОВ (импортируем из настроек)
# =============================================================================

# Лимиты фотографий для аватаров
AVATAR_MIN_PHOTOS: Final[int] = settings.AVATAR_MIN_PHOTOS
AVATAR_MAX_PHOTOS: Final[int] = settings.AVATAR_MAX_PHOTOS
AVATAR_MAX_PHOTOS_PER_USER: Final[int] = settings.AVATAR_MAX_PHOTOS_PER_USER

# Ограничения файлов
PHOTO_MAX_SIZE: Final[int] = settings.PHOTO_MAX_SIZE
PHOTO_MIN_RESOLUTION: Final[int] = settings.PHOTO_MIN_RESOLUTION
PHOTO_MAX_RESOLUTION: Final[int] = settings.PHOTO_MAX_RESOLUTION
PHOTO_ALLOWED_FORMATS: Final[list] = settings.PHOTO_ALLOWED_FORMATS

# Временные ограничения
AVATAR_CREATION_COOLDOWN: Final[int] = settings.AVATAR_CREATION_COOLDOWN  # 24 часа
PHOTO_UPLOAD_TIMEOUT: Final[int] = settings.PHOTO_UPLOAD_TIMEOUT  # 5 минут

# Пороги качества
MIN_FACE_SIZE: Final[int] = settings.MIN_FACE_SIZE
QUALITY_THRESHOLD: Final[float] = settings.QUALITY_THRESHOLD

# =============================================================================
# АУДИО И ФАЙЛОВЫЕ ЛИМИТЫ (импортируем из настроек)
# =============================================================================

# Аудио лимиты
MAX_AUDIO_SIZE: Final[int] = settings.MAX_AUDIO_SIZE  # 1GB
TELEGRAM_API_LIMIT: Final[int] = settings.TELEGRAM_API_LIMIT  # 20MB

# =============================================================================
# ПАКЕТЫ ПОПОЛНЕНИЯ (импортируем из настроек)
# =============================================================================

# Пакеты пополнения баланса
TOPUP_PACKAGES: Final[dict] = settings.TOPUP_PACKAGES
