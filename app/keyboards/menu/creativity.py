"""
Клавиатуры раздела "Творчество"

Структура творчества:
- 📷 Фото - создание изображений
- 🎬 Видео - создание видеороликов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_creativity_menu() -> InlineKeyboardMarkup:
    """
    🎨 Меню творчества - создание контента
    
    Основные направления творчества:
    - Фото (аватары и Imagen4)
    - Видео (различные платформы)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 Фото",
                callback_data="photo_menu"
            ),
            InlineKeyboardButton(
                text="🎬 Видео",
                callback_data="video_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="main_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_photo_menu() -> InlineKeyboardMarkup:
    """
    📷 Меню фото - создание изображений
    
    Переиспользует существующую структуру images_menu
    но с новыми callback_data для консистентности
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📷 Фото со мной",
                callback_data="avatar_generation_menu"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 По описанию",
                callback_data="imagen4_generation"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="🎬 Видео",
                callback_data="video_generation_stub"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="creativity_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_video_menu_v2() -> InlineKeyboardMarkup:
    """
    🎬 Новое меню видео - создание видеороликов
    
    Переиспользует существующие обработчики видео
    но с улучшенной навигацией
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎭 Hedra AI",
                callback_data="hedra_video"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="🌟 Kling",
                callback_data="kling_video"  # Переиспользуем существующий
            ),
            InlineKeyboardButton(
                text="🎪 Weo3",
                callback_data="weo3_video"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="📁 Мои видео",
                callback_data="my_videos"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="creativity_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


# LEGACY: Алиасы для обратной совместимости
# TODO: Удалить после рефакторинга всех импортов

def get_ai_creativity_menu() -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню творчества"""
    return get_creativity_menu()

def get_images_menu() -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню изображений"""
    return get_photo_menu()

def get_video_menu() -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню видео"""
    return get_video_menu_v2() 