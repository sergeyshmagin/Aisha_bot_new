"""
Клавиатуры раздела "Мои работы"

Структура проектов:
- 🖼️ Все фото - просмотр всех изображений
- 🎬 Все видео - просмотр всех видеороликов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_projects_menu() -> InlineKeyboardMarkup:
    """
    🎭 Меню "Мои работы" - результаты творчества
    
    Централизованное управление всеми созданными материалами:
    - Фото (аватары и Imagen4)
    - Видео (все платформы)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🖼️ Все фото",
                callback_data="all_photos"
            ),
            InlineKeyboardButton(
                text="🎬 Все видео",
                callback_data="all_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="⭐ Избранное",
                callback_data="favorites"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="my_stats"
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


def get_all_photos_menu() -> InlineKeyboardMarkup:
    """
    🖼️ Меню всех фото - просмотр изображений
    
    Переиспользует существующую галерею с новой навигацией
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📸 Фото со мной",
                callback_data="gallery_avatars"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ По описанию",
                callback_data="gallery_imagen"  # Переиспользуем существующий
            ),
            InlineKeyboardButton(
                text="🎬 Видео из фото",
                callback_data="gallery_video"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 По дате",
                callback_data="gallery_by_date"  # Переиспользуем существующий
            ),
            InlineKeyboardButton(
                text="⭐ Избранное",
                callback_data="favorites"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="projects_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_all_videos_menu() -> InlineKeyboardMarkup:
    """
    🎬 Меню всех видео - просмотр видеороликов
    
    Новый раздел для управления видео контентом
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎭 Hedra AI",
                callback_data="gallery_hedra_videos"
            ),
            InlineKeyboardButton(
                text="🌟 Kling",
                callback_data="gallery_kling_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎪 Weo3",
                callback_data="gallery_weo3_videos"
            ),
            InlineKeyboardButton(
                text="📁 Все видео",
                callback_data="my_videos"  # Переиспользуем существующий
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 По дате",
                callback_data="videos_by_date"
            ),
            InlineKeyboardButton(
                text="⭐ Избранное",
                callback_data="favorite_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="projects_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_favorites_menu() -> InlineKeyboardMarkup:
    """
    ⭐ Избранное - любимые работы пользователя
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Избранные образы",
                callback_data="favorites_avatars"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Избранные фото",
                callback_data="favorites_images"
            ),
            InlineKeyboardButton(
                text="🎬 Избранные видео",
                callback_data="favorites_videos"
            )
        ],
        [
            InlineKeyboardButton(
                text="🗂️ Коллекции",
                callback_data="favorites_collections"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="projects_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu_v2"
            )
        ]
    ])


# LEGACY: Алиасы для обратной совместимости
# TODO: Удалить после рефакторинга всех импортов

def get_my_projects_menu() -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню проектов"""
    return get_projects_menu()

def get_gallery_menu() -> InlineKeyboardMarkup:
    """LEGACY: Алиас для старого меню галереи"""
    return get_all_photos_menu() 