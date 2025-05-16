import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
STATE_FILE = os.getenv("STATE_FILE", "states.json")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Директория для хранения логов
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ID ассистента для GPT
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_dFIIdQIDNebZ4Qc5iHCE0Muq")
# <-- Укажите здесь ваш настоящий assistant_id

# --- FAL.AI интеграция ---
FAL_WEBHOOK_URL = os.getenv(
    "FAL_WEBHOOK_URL", "https://aibots.kz/api/avatar/status_update"
)
FAL_MODE = os.getenv("FAL_MODE", "character")
FAL_ITERATIONS = int(os.getenv("FAL_ITERATIONS", 500))
FAL_PRIORITY = os.getenv("FAL_PRIORITY", "quality")
FAL_CAPTIONING = os.getenv("FAL_CAPTIONING", "true").lower() == "true"
FAL_TRIGGER_WORD = os.getenv("FAL_TRIGGER_WORD", "TOK")
FAL_LORA_RANK = int(os.getenv("FAL_LORA_RANK", 32))
FAL_FINETUNE_TYPE = os.getenv("FAL_FINETUNE_TYPE", "full")
FAL_TRAINING_TEST_MODE = os.getenv("FAL_TRAINING_TEST_MODE", "false").lower() == "true"

# --- Пути ---
AVATAR_STORAGE_PATH = Path(os.getenv("AVATAR_STORAGE_PATH", STORAGE_DIR / "avatars"))
GALLERY_PATH = Path(os.getenv("GALLERY_PATH", AVATAR_STORAGE_PATH / "gallery"))
TRANSCRIPTS_PATH = Path(os.getenv("TRANSCRIPTS_PATH", STORAGE_DIR / "transcripts"))
THUMBNAIL_PATH = Path(os.getenv("THUMBNAIL_PATH", AVATAR_STORAGE_PATH / "thumbnails"))
AVATAR_DIR = os.getenv("AVATAR_DIR", "avatars")

# --- Лимиты файлов ---
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50 MB
MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", 3600))  # 1 час
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", 3600))  # 1 час
MAX_PHOTO_SIZE = int(os.getenv("MAX_PHOTO_SIZE", 20 * 1024 * 1024))  # 20 MB
ALLOWED_AUDIO_FORMATS = os.getenv("ALLOWED_AUDIO_FORMATS", "mp3,wav,ogg,m4a,flac,aac,wma,opus").split(",")
ALLOWED_VIDEO_FORMATS = os.getenv("ALLOWED_VIDEO_FORMATS", "mp4,mov,avi,mkv").split(",")
ALLOWED_PHOTO_FORMATS = os.getenv("ALLOWED_PHOTO_FORMATS", "jpg,jpeg,png").split(",")

# --- Лимиты аватаров ---
AVATAR_MIN_PHOTOS = int(os.getenv("AVATAR_MIN_PHOTOS", 10))
AVATAR_MAX_PHOTOS = int(os.getenv("AVATAR_MAX_PHOTOS", 20))
AVATARS_PER_PAGE = int(os.getenv("AVATARS_PER_PAGE", 3))
PHOTO_MAX_MB = int(os.getenv("PHOTO_MAX_MB", 20))
PHOTO_MIN_RES = int(os.getenv("PHOTO_MIN_RES", 512))
THUMBNAIL_SIZE = int(os.getenv("THUMBNAIL_SIZE", 256))

# --- Эмодзи ---
PROGRESSBAR_EMOJI_FILLED = os.getenv("PROGRESSBAR_EMOJI_FILLED", "🟩")
PROGRESSBAR_EMOJI_CURRENT = os.getenv("PROGRESSBAR_EMOJI_CURRENT", "🟦")
PROGRESSBAR_EMOJI_EMPTY = os.getenv("PROGRESSBAR_EMOJI_EMPTY", "⬜")

# --- Статусы ---
AVATAR_STATUS_TRAINING = os.getenv("AVATAR_STATUS_TRAINING", "Обучается...")
AVATAR_STATUS_READY = os.getenv("AVATAR_STATUS_READY", "Готов")
AVATAR_STATUS_ERROR = os.getenv("AVATAR_STATUS_ERROR", "Ошибка")

# --- Гендеры ---
AVATAR_GENDER_MALE = os.getenv("AVATAR_GENDER_MALE", "Мужской")
AVATAR_GENDER_FEMALE = os.getenv("AVATAR_GENDER_FEMALE", "Женский")
AVATAR_GENDER_OTHER = os.getenv("AVATAR_GENDER_OTHER", "Другое")

# --- Таймауты ---
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))

# --- Кэширование ---
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1 час
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", 1000))  # Максимальное количество элементов в кэше

TRANSCRIBE_DIR = os.getenv("TRANSCRIBE_DIR", "transcribe")
HISTORY_DIR = Path(os.getenv("HISTORY_DIR", STORAGE_DIR / "history"))

# --- Redis конфигурация ---
REDIS_HOST = os.getenv("REDIS_HOST", "192.168.0.3")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", 10))
REDIS_POOL_TIMEOUT = int(os.getenv("REDIS_POOL_TIMEOUT", 5))
REDIS_RETRY_ON_TIMEOUT = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
REDIS_MAX_RETRIES = int(os.getenv("REDIS_MAX_RETRIES", 3))
REDIS_RETRY_INTERVAL = int(os.getenv("REDIS_RETRY_INTERVAL", 1))

# Новые параметры конфигурации
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "temp"

# Создаем необходимые директории
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Telegram
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TEST_DB = 1  # Отдельная БД для тестов

# Логирование
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
REDIS_LOG_TTL = 7 * 24 * 60 * 60  # 7 дней

# Whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

# OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Настройки бота
MAX_MESSAGE_LENGTH = 4096
MAX_VOICE_DURATION = 300  # секунд
SUPPORTED_LANGUAGES = ["ru", "en"]
DEFAULT_LANGUAGE = "ru"

# Настройки кэширования
MAX_CACHE_SIZE = 1000  # максимальное количество записей

# Настройки очередей
QUEUE_PREFIX = "queue:"
MAX_RETRIES = 3
RETRY_DELAY = 60  # секунд

# Настройки безопасности
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

# Настройки мониторинга
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "aisha")
POSTGRES_USER = os.getenv("POSTGRES_USER", "aisha_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Баланс
INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "100.0"))  # Начальный баланс в монетах
MIN_BALANCE = float(os.getenv("MIN_BALANCE", "0.0"))  # Минимальный баланс
COIN_PRICE = float(os.getenv("COIN_PRICE", "1.0"))  # Цена одной монеты в рублях

# Сервисы
AVATAR_CREATION_COST = float(os.getenv("AVATAR_CREATION_COST", "10.0"))  # Стоимость создания аватара
TRANSCRIPT_COST = float(os.getenv("TRANSCRIPT_COST", "5.0"))  # Стоимость транскрибации
PHOTO_ENHANCE_COST = float(os.getenv("PHOTO_ENHANCE_COST", "3.0"))  # Стоимость улучшения фото
