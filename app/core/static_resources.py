"""
Конфигурация статических ресурсов бота
"""
from pathlib import Path
from app.core.config import settings

class StaticResources:
    """Управление статическими ресурсами"""
    
    @staticmethod
    def get_static_dir() -> Path:
        """Получить путь к папке со статическими файлами"""
        return settings.BASE_DIR / "storage" / "static"
    
    @staticmethod
    def get_images_dir() -> Path:
        """Получить путь к папке с изображениями"""
        return StaticResources.get_static_dir() / "images"
    
    @staticmethod
    def get_aisha_avatar_path() -> Path:
        """Получить путь к аватару Аиши"""
        return StaticResources.get_images_dir() / "aisha_avatar.jpg"
    
    @staticmethod
    def ensure_static_dirs():
        """Создать папки для статических ресурсов если их нет"""
        StaticResources.get_images_dir().mkdir(parents=True, exist_ok=True)

# Инициализируем папки при импорте модуля
StaticResources.ensure_static_dirs() 