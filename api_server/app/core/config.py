"""
Конфигурация API сервера для обработки webhook от FAL AI
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Настройки API сервера"""
    
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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/aisha_bot")
    
    # Telegram Bot
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    
    # FAL AI настройки
    FAL_API_KEY: str = os.getenv("FAL_API_KEY", "")
    FAL_WEBHOOK_SECRET: str = os.getenv("FAL_WEBHOOK_SECRET", "")  # Дополнительная безопасность
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    WEBHOOK_LOG_FILE: str = "webhook.log"
    
    # Безопасность
    ALLOWED_IPS: list = ["185.199.108.0/22", "140.82.112.0/20"]  # IP адреса FAL AI
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем глобальный экземпляр настроек
settings = Settings()

# Абсолютные пути к SSL сертификатам
API_SERVER_ROOT = Path(__file__).parent.parent.parent
SSL_CERT_FULL_PATH = API_SERVER_ROOT / settings.SSL_CERT_PATH
SSL_KEY_FULL_PATH = API_SERVER_ROOT / settings.SSL_KEY_PATH
SSL_CA_BUNDLE_FULL_PATH = API_SERVER_ROOT / settings.SSL_CA_BUNDLE_PATH 