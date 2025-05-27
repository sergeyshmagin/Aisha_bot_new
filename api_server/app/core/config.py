"""
Конфигурация API сервера для обработки webhook от FAL AI
Обновленная версия для продакшн использования
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    """Настройки API сервера"""
    
    # Конфигурация модели - игнорируем лишние поля из .env
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Игнорируем лишние поля
    )
    
    # API Server настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8443  # HTTPS порт для SSL
    API_DEBUG: bool = False
    API_RELOAD: bool = False
    
    # SSL настройки для FAL AI webhook
    SSL_ENABLED: bool = True
    SSL_CERT_PATH: str = "ssl/aibots_kz.crt"
    SSL_KEY_PATH: str = "ssl/aibots.kz.key"
    SSL_CA_BUNDLE_PATH: str = "ssl/aibots_kz.ca-bundle"
    
    # Database URL (используем ту же БД что и основной бот)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://aisha_user:secure_password@localhost/aisha_v2")
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # FAL AI настройки
    FAL_API_KEY: str = os.getenv("FAL_API_KEY", "")
    FAL_KEY: str = os.getenv("FAL_KEY", "")  # Альтернативное имя
    FAL_WEBHOOK_URL: str = os.getenv("FAL_WEBHOOK_URL", "https://aibots.kz:8443/api/v1/avatar/status_update")
    FAL_WEBHOOK_SECRET: str = os.getenv("FAL_WEBHOOK_SECRET", "")
    
    # MinIO настройки (для загрузки архивов)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET_AVATARS: str = os.getenv("MINIO_BUCKET_AVATARS", "aisha-v2-avatars")
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    WEBHOOK_LOG_FILE: str = "webhook.log"
    API_LOG_FILE: str = "api.log"
    
    # Тестовый режим
    FAL_TRAINING_TEST_MODE: bool = os.getenv("FAL_TRAINING_TEST_MODE", "false").lower() == "true"
    
    @property
    def effective_fal_api_key(self) -> str:
        """Возвращает FAL API ключ из любого доступного источника"""
        return self.FAL_API_KEY or self.FAL_KEY or ""

# Создаем глобальный экземпляр настроек
settings = Settings()

# Абсолютные пути к SSL сертификатам
API_SERVER_ROOT = Path(__file__).parent.parent.parent
SSL_CERT_FULL_PATH = API_SERVER_ROOT / settings.SSL_CERT_PATH
SSL_KEY_FULL_PATH = API_SERVER_ROOT / settings.SSL_KEY_PATH
SSL_CA_BUNDLE_FULL_PATH = API_SERVER_ROOT / settings.SSL_CA_BUNDLE_PATH 