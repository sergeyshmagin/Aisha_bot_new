"""
Клавиатуры для системы аватаров (чистая версия)
Исправленная версия без синтаксических ошибок
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import AvatarStatus


def get_avatar_main_menu(avatars_count: int = 0) -> InlineKeyboardMarkup:
    """Главное меню системы аватаров (упрощенное с портретной моделью)"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🎭 Создать аватар",
                callback_data="create_avatar"
            )
        ]
    ]
    
    if avatars_count > 0:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎭 Мои аватары ({avatars_count})",
                callback_data="avatar_gallery"
            )
        ])
    
    buttons.extend([
        [
            InlineKeyboardButton(
                text="❓ Как работает?",
                callback_data="avatar_help"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="creativity_menu"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_avatar_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола аватара (упрощенная без выбора модели)"""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👨 Мужской",
                callback_data="avatar_gender_male"
            ),
            InlineKeyboardButton(
                text="👩 Женский",
                callback_data="avatar_gender_female"
            )
        ],
        [
            InlineKeyboardButton(
                text="💡 Зачем выбирать?",
                callback_data="explain_gender_choice"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="back_to_avatar_menu"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_avatar_creation"
            )
        ]
    ])


def get_avatar_gallery_keyboard(current_page: int, total_pages: int, avatars_on_page: int) -> InlineKeyboardMarkup:
    """Клавиатура галереи аватаров"""
    
    buttons = []
    
    # Навигация по страницам
    if total_pages > 1:
        nav_buttons = []
        
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"avatar_page_{current_page - 1}"
                )
            )
        
        nav_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page}/{total_pages}",
                callback_data="page_info"
            )
        )
        
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"avatar_page_{current_page + 1}"
                )
            )
        
        buttons.append(nav_buttons)
    
    # Создать новый аватар
    buttons.append([
        InlineKeyboardButton(
            text="🆕 Создать новый",
            callback_data="create_avatar"
        )
    ])
    
    # Назад
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К меню аватаров",
            callback_data="avatar_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_avatar_actions_keyboard(avatar_id: str, status: AvatarStatus) -> InlineKeyboardMarkup:
    """Клавиатура действий с аватаром"""
    
    buttons = []
    
    # Действия в зависимости от статуса
    if status == "completed":
        buttons.append([
            InlineKeyboardButton(
                text="📷 Сделать фото",
                callback_data=f"generate_image_{avatar_id}"
            )
        ])
    elif status == "training":
        buttons.append([
            InlineKeyboardButton(
                text="📊 Прогресс обучения",
                callback_data=f"training_progress_{avatar_id}"
            )
        ])
    elif status == "ready_for_training":
        buttons.append([
            InlineKeyboardButton(
                text="🚀 Начать обучение",
                callback_data=f"start_training_{avatar_id}"
            )
        ])
    elif status == "photos_uploading":
        buttons.append([
            InlineKeyboardButton(
                text="📸 Продолжить загрузку",
                callback_data=f"continue_upload_{avatar_id}"
            )
        ])
    
    # Общие действия
    buttons.append([
        InlineKeyboardButton(
            text="📝 Редактировать",
            callback_data=f"edit_avatar_{avatar_id}"
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_avatar_{avatar_id}"
        )
    ])
    
    # Назад
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К галерее",
            callback_data="avatar_gallery"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard(action: str, target_id: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура подтверждения действия"""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, подтверждаю",
                callback_data=f"confirm_{action}_{target_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"cancel_{action}_{target_id}"
            )
        ]
    ])


# Экспорт основных функций
__all__ = [
    "get_avatar_main_menu",
    "get_avatar_gender_keyboard",
    "get_avatar_gallery_keyboard",
    "get_avatar_actions_keyboard",
    "get_confirmation_keyboard"
] 