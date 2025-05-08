import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Директория для хранения логов
LOG_DIR = os.getenv('LOG_DIR', 'logs')

# Уровень логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# ID ассистента для GPT
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_dFIIdQIDNebZ4Qc5iHCE0Muq")
# <-- Укажите здесь ваш настоящий assistant_id

# --- FAL.AI интеграция ---
FAL_WEBHOOK_URL = os.getenv(
    "FAL_WEBHOOK_URL", f"{BACKEND_URL}/api/avatar/status_update"
)
FAL_MODE = os.getenv("FAL_MODE", "character")
FAL_ITERATIONS = int(os.getenv("FAL_ITERATIONS", 300))
FAL_PRIORITY = os.getenv("FAL_PRIORITY", "quality")
FAL_CAPTIONING = os.getenv("FAL_CAPTIONING", "true").lower() == "true"
FAL_TRIGGER_WORD = os.getenv("FAL_TRIGGER_WORD", "TOK")
FAL_LORA_RANK = int(os.getenv("FAL_LORA_RANK", 32))
FAL_FINETUNE_TYPE = os.getenv("FAL_FINETUNE_TYPE", "full")

# --- Пути ---
AVATAR_STORAGE_PATH = os.getenv("AVATAR_STORAGE_PATH", "storage/avatars")
GALLERY_PATH = os.getenv(
    "GALLERY_PATH", AVATAR_STORAGE_PATH + "/gallery"
)
TRANSCRIPTS_PATH = os.getenv("TRANSCRIPTS_PATH", "storage/transcripts")
THUMBNAIL_PATH = os.getenv(
    "THUMBNAIL_PATH", AVATAR_STORAGE_PATH + "/thumbnails"
)

# --- Лимиты ---
AVATAR_MIN_PHOTOS = int(os.getenv("AVATAR_MIN_PHOTOS", 8))
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
