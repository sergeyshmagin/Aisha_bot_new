from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """
    Создает главное меню бота с inline-кнопками.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🤖 Бизнес-ассистент",
                callback_data="business_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼 Галерея",
                callback_data="business_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🧑‍🎨 Аватары",
                callback_data="business_avatar"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="main_help"
            )
        ]
    ]) 