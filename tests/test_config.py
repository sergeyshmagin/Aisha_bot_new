"""
Конфигурация для тестов.
"""

import os
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    """Настройки для тестов."""
    
    # Настройки для тестовой базы данных
    TEST_POSTGRES_USER: str = "aisha_user"
    TEST_POSTGRES_PASSWORD: str = "test_password"
    TEST_POSTGRES_HOST: str = "192.168.0.4"
    TEST_POSTGRES_PORT: str = "5432"
    TEST_POSTGRES_DB: str = "aisha_test"
    
    # URL для тестовой базы данных
    @property
    def DATABASE_URL(self) -> str:
        """Получаем URL для тестовой базы данных."""
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}@{self.TEST_POSTGRES_HOST}:{self.TEST_POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
    
    # Настройки для Redis
    TEST_REDIS_HOST: str = "localhost"
    TEST_REDIS_PORT: int = 6379
    TEST_REDIS_DB: int = 1
    
    # Настройки для Telegram
    TEST_TELEGRAM_BOT_TOKEN: str = "test_token"
    TEST_TELEGRAM_CHAT_ID: int = 123456789
    
    class Config:
        """Конфигурация для загрузки переменных окружения."""
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

# Создаем экземпляр настроек для тестов
test_settings = TestSettings() 