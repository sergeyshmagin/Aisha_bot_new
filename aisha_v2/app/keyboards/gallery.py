from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_gallery_menu() -> InlineKeyboardMarkup:
    """
    Создает меню галереи с inline-кнопками.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура меню галереи
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🖼 Мои изображения",
                callback_data="gallery_my_images"
            )
        ],
        [
            InlineKeyboardButton(
                text="📤 Загрузить",
                callback_data="gallery_upload"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Поиск",
                callback_data="gallery_search"
            )
        ],
        [
            InlineKeyboardButton(
                text="📁 Папки",
                callback_data="gallery_folders"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_main"
            )
        ]
    ]) 