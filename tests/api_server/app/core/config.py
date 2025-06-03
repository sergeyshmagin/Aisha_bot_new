"""
Конфигурация API сервера для обработки webhook от FAL AI
Обновленная версия для продакшн использования
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, validator
from typing import Dict, Any, Optional

class Settings(BaseSettings):
    """Настройки API сервера"""
    
    # Конфигурация модели - игнорируем лишние поля из .env
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Игнорируем лишние поля
    )
    
    # API Server настройки (читаем из переменных окружения)
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))  # По умолчанию 8000 для Nginx проксирования
    API_DEBUG: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    
    # SSL настройки для FAL AI webhook (читаем из переменных окружения)
    SSL_ENABLED: bool = os.getenv("SSL_ENABLED", "false").lower() == "true"  # По умолчанию false (SSL в Nginx)
    SSL_CERT_PATH: str = os.getenv("SSL_CERT_PATH", "ssl/aibots_kz.crt")
    SSL_KEY_PATH: str = os.getenv("SSL_KEY_PATH", "ssl/aibots.kz.key")
    SSL_CA_BUNDLE_PATH: str = os.getenv("SSL_CA_BUNDLE_PATH", "ssl/aibots_kz.ca-bundle")
    
    # PostgreSQL настройки (синхронизированы с основным ботом)
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST", "192.168.0.4")
    POSTGRES_PORT: Optional[int] = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB", "aisha")
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER", "aisha_user")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD", "KbZZGJHX09KSH7r9ev4m")
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Автоматически собираем DATABASE_URL из переменных PostgreSQL (как в основном боте)"""
        if isinstance(v, str) and v:
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # FAL AI настройки
    FAL_API_KEY: str = os.getenv("FAL_API_KEY", "")
    FAL_KEY: str = os.getenv("FAL_KEY", "")  # Альтернативное имя
    FAL_WEBHOOK_URL: str = os.getenv("FAL_WEBHOOK_URL", "https://aibots.kz:8443/api/v1/avatar/status_update")
    FAL_WEBHOOK_SECRET: str = os.getenv("FAL_WEBHOOK_SECRET", "")
    
    # MinIO настройки (синхронизированы с основным ботом)
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "192.168.0.4:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET_AVATARS: str = os.getenv("MINIO_BUCKET_AVATARS", "avatars")
    
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