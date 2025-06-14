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


def get_photo_menu(avatar_photos_count: int = None, imagen_photos_count: int = None, avatars_count: int = None) -> InlineKeyboardMarkup:
    """
    📷 Меню фото - создание изображений
    
    Переиспользует существующую структуру images_menu
    но с новыми callback_data для консистентности
    
    Args:
        avatar_photos_count: Количество фото с аватаром для отображения в скобках
        imagen_photos_count: Количество фото по описанию для отображения в скобках  
        avatars_count: Количество аватаров для отображения в кнопке "Мои аватары"
    """
    # Формируем текст кнопок с количеством
    avatar_text = "📷 Фото с аватаром"
    if avatar_photos_count is not None and avatar_photos_count > 0:
        avatar_text = f"📷 Фото с аватаром ({avatar_photos_count})"
    
    imagen_text = "📝 По описанию"
    if imagen_photos_count is not None and imagen_photos_count > 0:
        imagen_text = f"📝 По описанию ({imagen_photos_count})"
    
    my_avatars_text = "🎭 Мои аватары"
    if avatars_count is not None and avatars_count > 0:
        my_avatars_text = f"🎭 Мои аватары ({avatars_count})"
    
    buttons = [
        [
            InlineKeyboardButton(
                text=avatar_text,
                callback_data="avatar_generation_menu"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text=imagen_text,
                callback_data="imagen4_generation"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text=my_avatars_text,
                callback_data="avatar_menu"  # Меню аватаров
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Мои фото",
                callback_data="all_photos"
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
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_video_menu_v2(videos_count: int = None) -> InlineKeyboardMarkup:
    """
    🎬 Новое меню видео - создание видеороликов
    
    Переиспользует существующие обработчики видео
    но с улучшенной навигацией
    
    Args:
        videos_count: Количество видео для отображения в кнопке "Мои видео"
    """
    # Формируем текст кнопки "Мои видео"
    my_videos_text = "📁 Мои видео"
    if videos_count is not None and videos_count > 0:
        my_videos_text = f"📁 Мои видео ({videos_count})"
    
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
                text=my_videos_text,
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

def get_video_menu(videos_count: int = None) -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню видео"""
    return get_video_menu_v2(videos_count=videos_count) 