from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """
    Создает обновленное главное меню бота с разделением функций.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Создать изображение",
                callback_data="generation_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 Мои аватары",
                callback_data="avatar_menu"
            ),
            InlineKeyboardButton(
                text="🖼️ Моя галерея",
                callback_data="my_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Личный кабинет",
                callback_data="profile_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎤 Транскрибация",
                callback_data="transcribe_menu"
            ),
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="main_help"
            )
        ]
    ]) 