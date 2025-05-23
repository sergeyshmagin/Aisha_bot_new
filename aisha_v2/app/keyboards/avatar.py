"""
Клавиатуры для работы с аватарами
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aisha_v2.app.database.models import AvatarType, AvatarStatus


def get_avatar_main_menu(avatars_count: int = 0) -> InlineKeyboardMarkup:
    """
    Главное меню аватаров с улучшенным UX
    
    Args:
        avatars_count: Количество аватаров пользователя
        
    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    avatar_text = f"📁 Мои аватары ({avatars_count})" if avatars_count > 0 else "📁 Мои аватары"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🆕 Создать аватар",
                callback_data="avatar_create"
            )
        ],
        [
            InlineKeyboardButton(
                text=avatar_text,
                callback_data="avatar_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Генерировать изображение",
                callback_data="avatar_generate"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="back_to_main"
            )
        ]
    ])


def get_avatar_type_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора типа аватара
    
    Returns:
        InlineKeyboardMarkup: Клавиатура выбора типа
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Персонаж",
                callback_data=f"avatar_type_{AvatarType.CHARACTER.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Стиль",
                callback_data=f"avatar_type_{AvatarType.STYLE.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Кастомный",
                callback_data=f"avatar_type_{AvatarType.CUSTOM.value}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="avatar_menu"
            )
        ]
    ])


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора пола аватара
    """
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
                text="🤖 Другое",
                callback_data="avatar_gender_other"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="avatar_type_selection"
            )
        ]
    ])


def get_photo_upload_keyboard(photos_count: int, min_photos: int, max_photos: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для управления загрузкой фотографий
    
    Args:
        photos_count: Текущее количество фотографий
        min_photos: Минимальное количество фотографий
        max_photos: Максимальное количество фотографий
        
    Returns:
        InlineKeyboardMarkup: Клавиатура для загрузки фото
    """
    buttons = []
    
    # Кнопка добавления фото (если не достигнут максимум)
    if photos_count < max_photos:
        buttons.append([
            InlineKeyboardButton(
                text="📤 Добавить фото",
                callback_data="avatar_add_photos"
            )
        ])
    
    # Кнопка просмотра (если есть фото)
    if photos_count > 0:
        buttons.append([
            InlineKeyboardButton(
                text="👁️ Просмотр галереи",
                callback_data="avatar_photos_gallery"
            )
        ])
    
    # Кнопка готово (если достигнут минимум)
    if photos_count >= min_photos:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Готово к обучению",
                callback_data="avatar_photos_ready"
            )
        ])
    
    # Кнопка назад
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="avatar_setup"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_photo_gallery_keyboard(current_page: int, total_pages: int, avatar_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по галерее фотографий
    
    Args:
        current_page: Текущая страница
        total_pages: Общее количество страниц
        avatar_id: ID аватара
        
    Returns:
        InlineKeyboardMarkup: Клавиатура галереи
    """
    buttons = []
    
    # Навигация
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"avatar_gallery_prev_{avatar_id}_{current_page-1}"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )
    
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"avatar_gallery_next_{avatar_id}_{current_page+1}"
            )
        )
    
    buttons.append(nav_buttons)
    
    # Действия
    buttons.append([
        InlineKeyboardButton(
            text="🗑️ Удалить фото",
            callback_data=f"avatar_photo_delete_{avatar_id}"
        ),
        InlineKeyboardButton(
            text="📤 Добавить еще",
            callback_data=f"avatar_add_more_{avatar_id}"
        )
    ])
    
    # Назад
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К загрузке",
            callback_data=f"avatar_upload_photos_{avatar_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_training_confirmation_keyboard(avatar_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения начала обучения
    
    Args:
        avatar_id: ID аватара
        
    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Начать обучение",
                callback_data=f"avatar_start_training_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки обучения",
                callback_data=f"avatar_training_settings_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Вернуться к фото",
                callback_data=f"avatar_upload_photos_{avatar_id}"
            )
        ]
    ])


def get_training_progress_keyboard(avatar_id: str, show_cancel: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура для мониторинга прогресса обучения
    
    Args:
        avatar_id: ID аватара
        show_cancel: Показывать ли кнопку отмены
        
    Returns:
        InlineKeyboardMarkup: Клавиатура прогресса
    """
    buttons = []
    
    # Обновить прогресс
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=f"avatar_training_progress_{avatar_id}"
        )
    ])
    
    # Отмена обучения (если доступна)
    if show_cancel:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить обучение", 
                callback_data=f"avatar_cancel_training_{avatar_id}"
            )
        ])
    
    # Назад к меню
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К списку аватаров",
            callback_data="avatar_gallery"
        ),
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="back_to_main"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_avatar_actions_keyboard(avatar_id: str, status: AvatarStatus) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с готовым аватаром
    
    Args:
        avatar_id: ID аватара
        status: Текущий статус аватара
        
    Returns:
        InlineKeyboardMarkup: Клавиатура действий
    """
    buttons = []
    
    # Генерация (только для завершенных аватаров)
    if status == AvatarStatus.COMPLETED:
        buttons.append([
            InlineKeyboardButton(
                text="🎨 Генерировать изображение",
                callback_data=f"avatar_generate_image_{avatar_id}"
            )
        ])
        
        buttons.append([
            InlineKeyboardButton(
                text="👁️ Примеры работ",
                callback_data=f"avatar_examples_{avatar_id}"
            )
        ])
    
    # Настройки
    buttons.append([
        InlineKeyboardButton(
            text="⚙️ Настройки",
            callback_data=f"avatar_settings_{avatar_id}"
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"avatar_stats_{avatar_id}"
        )
    ])
    
    # Удаление
    buttons.append([
        InlineKeyboardButton(
            text="🗑️ Удалить аватар",
            callback_data=f"avatar_delete_{avatar_id}"
        )
    ])
    
    # Назад
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К списку аватаров",
            callback_data="avatar_gallery"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_generation_keyboard(avatar_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для генерации изображений
    
    Args:
        avatar_id: ID аватара
        
    Returns:
        InlineKeyboardMarkup: Клавиатура генерации
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎭 Портрет",
                callback_data=f"generate_portrait_{avatar_id}"
            ),
            InlineKeyboardButton(
                text="🌟 В полный рост",
                callback_data=f"generate_fullbody_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Кастомный промпт",
                callback_data=f"generate_custom_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки качества",
                callback_data=f"generate_settings_{avatar_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад к аватару",
                callback_data=f"avatar_details_{avatar_id}"
            )
        ]
    ])


def get_confirmation_keyboard(action: str, target_id: str) -> InlineKeyboardMarkup:
    """
    Универсальная клавиатура подтверждения действия
    
    Args:
        action: Действие для подтверждения
        target_id: ID объекта
        
    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения
    """
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


# Legacy функции для совместимости
def avatar_inline_keyboard():
    """Legacy функция - использовать get_avatar_main_menu"""
    return get_avatar_main_menu()


def get_avatar_menu() -> InlineKeyboardMarkup:
    """Legacy функция - использовать get_avatar_main_menu"""
    return get_avatar_main_menu() 