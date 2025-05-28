# LEGACY FILE - РЕФАКТОРЕН В МОДУЛИ
# Файл app/handlers/avatar/photo_upload.py (924 строки) рефакторен в модульную структуру
# Дата рефакторинга: 28 мая 2025
# Новая структура: app/handlers/avatar/photo_upload/

# Импорт для обратной совместимости
from .photo_upload.main_handler import PhotoUploadHandler

# Создаем экземпляр обработчика и router
photo_handler = PhotoUploadHandler()
router = photo_handler.router

# Регистрируем обработчики
import asyncio
asyncio.create_task(photo_handler.register_handlers())

# Экспорт для совместимости со старым кодом
__all__ = ["PhotoUploadHandler", "router", "photo_handler"]

# TODO: Удалить этот файл после тестирования новой модульной структуры 