"""
Утилиты для работы с аватарами
"""
import re
from datetime import datetime
from typing import Optional


def format_finetune_comment(avatar_name: str, telegram_username: str) -> str:
    """
    Формирует комментарий для обучения аватара в FAL AI
    
    Args:
        avatar_name: Имя аватара
        telegram_username: Username пользователя в Telegram (может содержать @)
    
    Returns:
        Отформатированный комментарий в формате "Имя - @username"
    
    Examples:
        >>> format_finetune_comment("Анна", "ivan_petrov")
        "Анна - @ivan_petrov"
        >>> format_finetune_comment("Художник", "@maria_art")
        "Художник - @maria_art"
    """
    # Очищаем имя аватара от спецсимволов, оставляем только буквы, цифры, пробелы, дефисы и подчеркивания
    clean_name = re.sub(r'[^\w\s\-_]', '', avatar_name).strip()[:30]
    
    # Очищаем username от лишних символов
    clean_username = telegram_username.replace('@', '').strip()
    clean_username = re.sub(r'[^\w]', '', clean_username)
    
    # Если имя пустое после очистки, используем дефолтное
    if not clean_name:
        clean_name = "Аватар"
    
    # Если username пустой, используем дефолтное
    if not clean_username:
        clean_username = "user"
    
    return f"{clean_name} - @{clean_username}"


def format_finetune_comment_detailed(
    avatar_name: str, 
    telegram_username: str, 
    avatar_type: str = "character"
) -> str:
    """
    Формирует подробный комментарий с типом аватара
    
    Args:
        avatar_name: Имя аватара
        telegram_username: Username пользователя
        avatar_type: Тип аватара (character, style, portrait)
    
    Returns:
        Подробный комментарий в формате "Тип: Имя (@username)"
    """
    type_names = {
        "character": "Персонаж",
        "style": "Стиль", 
        "portrait": "Портрет",
        "general": "Общий"
    }
    
    type_name = type_names.get(avatar_type, "Аватар")
    basic_comment = format_finetune_comment(avatar_name, telegram_username)
    
    return f"{type_name}: {basic_comment}"


def format_finetune_comment_debug(
    avatar_name: str, 
    telegram_username: str, 
    avatar_id: str
) -> str:
    """
    Формирует комментарий с отладочной информацией
    
    Args:
        avatar_name: Имя аватара
        telegram_username: Username пользователя
        avatar_id: ID аватара
    
    Returns:
        Комментарий с датой и ID для отладки
    """
    basic_comment = format_finetune_comment(avatar_name, telegram_username)
    date = datetime.now().strftime("%d.%m")
    short_id = str(avatar_id).replace('-', '')[:8]
    
    return f"{basic_comment} ({date}, {short_id})"


def generate_trigger_word(avatar_id: str) -> str:
    """
    Генерирует уникальный trigger_word для аватара
    
    Args:
        avatar_id: UUID аватара
    
    Returns:
        Уникальный триггер в формате "TOK_xxxxxxxx"
    
    Examples:
        >>> generate_trigger_word("4a473199-ae2e-4b0d-a212-68fbd58877f4")
        "TOK_4a473199"
    """
    # Убираем дефисы и берем первые 8 символов
    short_id = str(avatar_id).replace('-', '')[:8]
    return f"TOK_{short_id}"


def generate_trigger_word_advanced(avatar_id: str, avatar_name: str) -> str:
    """
    Генерирует продвинутый trigger_word с частью имени
    
    Args:
        avatar_id: UUID аватара
        avatar_name: Имя аватара
    
    Returns:
        Триггер с именем в формате "TOK_name_id"
    """
    # Очищаем имя для использования в триггере
    clean_name = re.sub(r'[^\w]', '', avatar_name.lower())[:8]
    short_id = str(avatar_id).replace('-', '')[:6]
    
    if clean_name:
        return f"TOK_{clean_name}_{short_id}"
    else:
        return f"TOK_{short_id}"


def validate_avatar_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Валидирует имя аватара
    
    Args:
        name: Имя для проверки
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Имя аватара не может быть пустым"
    
    if len(name.strip()) < 2:
        return False, "Имя аватара должно содержать минимум 2 символа"
    
    if len(name.strip()) > 50:
        return False, "Имя аватара не может быть длиннее 50 символов"
    
    # Проверяем на недопустимые символы
    if re.search(r'[<>:"/\\|?*]', name):
        return False, "Имя содержит недопустимые символы"
    
    return True, None


def sanitize_username(username: str) -> str:
    """
    Очищает username от недопустимых символов
    
    Args:
        username: Username для очистки
    
    Returns:
        Очищенный username
    """
    if not username:
        return "user"
    
    # Убираем @ если есть
    clean = username.replace('@', '').strip()
    
    # Оставляем только буквы, цифры и подчеркивания
    clean = re.sub(r'[^\w]', '', clean)
    
    # Если после очистки ничего не осталось
    if not clean:
        return "user"
    
    return clean[:20]  # Ограничиваем длину


def get_avatar_type_display_name(avatar_type: str) -> str:
    """
    Возвращает отображаемое имя типа аватара
    
    Args:
        avatar_type: Тип аватара (style, portrait, character, etc.)
    
    Returns:
        Человекочитаемое название типа
    """
    type_names = {
        "style": "🎨 Художественный",
        "portrait": "🎭 Портретный", 
        "character": "👤 Персонаж",
        "general": "🌟 Общий",
        "product": "📦 Продукт"
    }
    
    return type_names.get(avatar_type, f"🤖 {avatar_type.title()}")


def format_training_duration(iterations: int, training_type: str = "style") -> str:
    """
    Оценивает примерное время обучения
    
    Args:
        iterations: Количество итераций
        training_type: Тип обучения
    
    Returns:
        Строка с примерным временем
    """
    # Примерные коэффициенты времени (в секундах на итерацию)
    time_coefficients = {
        "style": 1.2,      # flux-pro-trainer
        "portrait": 0.8,   # flux-lora-portrait-trainer
        "character": 1.0,
        "general": 1.5
    }
    
    coefficient = time_coefficients.get(training_type, 1.0)
    estimated_seconds = iterations * coefficient
    
    if estimated_seconds < 300:  # < 5 минут
        return f"~{int(estimated_seconds/60)} мин"
    elif estimated_seconds < 1800:  # < 30 минут
        return f"~{int(estimated_seconds/60)} мин"
    else:  # > 30 минут
        hours = int(estimated_seconds / 3600)
        minutes = int((estimated_seconds % 3600) / 60)
        if hours > 0:
            return f"~{hours}ч {minutes}мин"
        else:
            return f"~{minutes} мин"


# Экспорт основных функций
__all__ = [
    "format_finetune_comment",
    "format_finetune_comment_detailed", 
    "format_finetune_comment_debug",
    "generate_trigger_word",
    "generate_trigger_word_advanced",
    "validate_avatar_name",
    "sanitize_username",
    "get_avatar_type_display_name",
    "format_training_duration"
] 