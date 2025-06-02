"""
Конфигурация приложения
"""
import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
    """Настройки приложения"""
