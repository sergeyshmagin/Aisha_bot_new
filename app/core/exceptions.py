"""
Кастомные исключения
LEGACY: Файл рефакторен в модульную структуру app/core/exceptions/
Этот файл обеспечивает обратную совместимость импортов.

Удалить после тестирования новой структуры!
"""

# Импорт из новой модульной структуры для обратной совместимости
from .exceptions.base_exceptions import *
from .exceptions.audio_exceptions import *
from .exceptions.storage_exceptions import *
from .exceptions.validation_exceptions import *
from .exceptions.config_exceptions import *
from .exceptions.avatar_exceptions import *
