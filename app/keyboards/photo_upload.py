"""
Клавиатуры для загрузки фотографий аватаров
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_photo_upload_keyboard(photos_count: int, min_photos: int, max_photos: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления загрузкой фотографий"""
    
    buttons = []
    
    # Показ галереи (если есть фото)
    if photos_count > 0:
        buttons.append([
            InlineKeyboardButton(
                text=f"🖼️ Галерея ({photos_count})",
                callback_data="show_photo_gallery"
            )
        ])
    
    # Кнопка завершения (если достаточно фото)
    if photos_count >= min_photos:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Готово к обучению!",
                callback_data=f"confirm_training_current"
            )
        ])
    
    # Дополнительные действия
    if photos_count < max_photos:
        buttons.append([
            InlineKeyboardButton(
                text="💡 Советы по фото",
                callback_data="photo_tips"
            )
        ])
    
    # Навигация
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Отмена",
            callback_data="avatar_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_photo_tips_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для советов по фотографиям"""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📸 Требования к фото",
                callback_data="photo_requirements"
            )
        ],
        [
            InlineKeyboardButton(
                text="💡 Советы по качеству",
                callback_data="photo_quality_tips"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Что избегать",
                callback_data="photo_avoid_tips"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к загрузке",
                callback_data="back_to_upload"
            )
        ]
    ])


def get_photo_gallery_navigation_keyboard(current_photo: int, total_photos: int, avatar_id: str) -> InlineKeyboardMarkup:
    """Клавиатура навигации по галерее фотографий с улучшенными кнопками"""
    
    buttons = []
    
    # Навигация по фото - улучшенная логика как в archive/aisha_v1
    nav_buttons = []
    if current_photo > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="gallery_nav_prev"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"📷 {current_photo}/{total_photos}",
            callback_data="photo_counter"
        )
    )
    
    if current_photo < total_photos:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data="gallery_nav_next"
            )
        )
    
    buttons.append(nav_buttons)
    
    # Действия с фото - как в старом проекте
    buttons.append([
        InlineKeyboardButton(
            text="🗑️ Удалить фото",
            callback_data=f"delete_photo_{avatar_id}_{current_photo}"
        )
    ])
    
    # Управление галереей  
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К загрузке",
            callback_data="back_to_upload"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_training_start_keyboard(avatar_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для начала обучения аватара"""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Да, начать обучение!",
                callback_data=f"start_training_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📸 Добавить еще фото",
                callback_data="continue_photo_upload"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Отмена",
                callback_data="avatar_menu"
            )
        ]
    ]) 