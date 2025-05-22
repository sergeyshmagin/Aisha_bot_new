"""
Основной модуль конфигурации.
Экспортирует все настройки из подмодулей.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field

from .base import BaseConfig
from .database import DatabaseConfig
from .storage import StorageConfig
from .external_services import ExternalServicesConfig

class Settings(BaseConfig, DatabaseConfig, StorageConfig, ExternalServicesConfig):
    """Объединенные настройки приложения"""
    
    # Пути
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    PYTHONPATH: Optional[str] = Field(None, env="PYTHONPATH")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем глобальный объект настроек только если не в тестовом режиме
if not os.getenv("TESTING"):
    settings = Settings()
else:
    from .test_config import TestConfig
    settings = TestConfig()

# Экспортируем все настройки
__all__ = ["settings"] 