"""
Модели данных и константы для основного обработчика транскриптов
Выделено из app/handlers/transcript_main.py для соблюдения правила ≤500 строк
"""
from typing import Dict, Any, Optional
from datetime import datetime


class TranscriptMainConfig:
    """Конфигурация для основного обработчика транскриптов"""
    
    PAGE_SIZE = 5
    MAX_FILENAME_LENGTH = 20
    PREVIEW_LENGTH = 300
    
    # Иконки для типов файлов
    TYPE_ICONS = {
        "audio": "🎵",
        "text": "📝",
        "unknown": "📄"
    }
    
    # Названия типов
    TYPE_NAMES = {
        "audio": "Аудио", 
        "text": "Текст",
        "unknown": "Файл"
    }


class TranscriptDisplayData:
    """Класс для форматирования данных транскрипта для отображения"""
    
    def __init__(self, transcript_data: Dict[str, Any]):
        self.data = transcript_data
        self.metadata = transcript_data.get("metadata", {})
        
    @property
    def id(self) -> str:
        """ID транскрипта"""
        return str(self.data.get("id", ""))
    
    @property
    def source(self) -> str:
        """Источник транскрипта (audio/text)"""
        return self.metadata.get("source", "unknown")
    
    @property
    def original_filename(self) -> str:
        """Оригинальное имя файла"""
        return self.metadata.get("file_name", "")
    
    @property
    def word_count(self) -> Optional[int]:
        """Количество слов"""
        return self.metadata.get("word_count")
    
    @property
    def created_at(self) -> str:
        """Дата создания"""
        return self.data.get("created_at", "")
    
    @property
    def formatted_date(self) -> str:
        """Отформатированная дата создания"""
        try:
            if isinstance(self.created_at, str):
                # Убираем микросекунды и временную зону для упрощения
                clean_date = self.created_at.split('.')[0].replace('T', ' ')
                dt = datetime.fromisoformat(clean_date)
                return dt.strftime("%d.%m %H:%M")
            else:
                return "—"
        except Exception:
            return "—"
    
    @property
    def type_icon(self) -> str:
        """Иконка типа файла"""
        return TranscriptMainConfig.TYPE_ICONS.get(self.source, "📄")
    
    @property
    def type_name(self) -> str:
        """Название типа файла"""
        return TranscriptMainConfig.TYPE_NAMES.get(self.source, "Файл")
    
    def get_friendly_filename(self) -> str:
        """
        Форматирует название файла для дружелюбного отображения пользователю
        
        Returns:
            Дружелюбное название файла
        """
        # Пытаемся извлечь осмысленное название из оригинального файла
        if self.original_filename:
            # Убираем расширение
            name_without_ext = self.original_filename.rsplit('.', 1)[0]
            
            # Если это техническое название вроде "2025-05-21_10-01_file_362"
            if '_file_' in name_without_ext or name_without_ext.count('_') >= 2:
                # Используем просто тип и дату
                friendly_name = f"{self.type_icon} {self.type_name}"
            else:
                # Используем оригинальное название, но сокращаем если длинное
                if len(name_without_ext) > TranscriptMainConfig.MAX_FILENAME_LENGTH:
                    friendly_name = f"{self.type_icon} {name_without_ext[:17]}..."
                else:
                    friendly_name = f"{self.type_icon} {name_without_ext}"
        else:
            # Fallback к типу файла
            friendly_name = f"{self.type_icon} {self.type_name}"
        
        # Добавляем количество слов для текстовых файлов
        if self.word_count and self.source == "text":
            friendly_name += f" ({self.word_count} сл.)"
        
        return f"{friendly_name} • {self.formatted_date}"


class UserRegistrationData:
    """Данные для регистрации пользователя"""
    
    def __init__(self, telegram_user):
        self.telegram_user = telegram_user
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь для регистрации"""
        return {
            "id": self.telegram_user.id,
            "username": self.telegram_user.username,
            "first_name": self.telegram_user.first_name,
            "last_name": self.telegram_user.last_name,
            "language_code": self.telegram_user.language_code or "ru",
            "is_bot": self.telegram_user.is_bot,
            "is_premium": getattr(self.telegram_user, "is_premium", False)
        } 