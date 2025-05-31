"""
LEGACY: Клавиатура старой галереи
ЗАМЕНЕНО НА: Новую систему генерации изображений  
ДАТА DEPRECATION: 2025-01-XX

Этот файл больше не используется в новой архитектуре.
Новая галерея реализована в:
- app/handlers/generation/main_handler.py 
- app/handlers/main_menu.py

TODO: Удалить после полного перехода на новую систему
"""

# LEGACY CODE - ЗАКОММЕНТИРОВАНО
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# def get_gallery_menu() -> InlineKeyboardMarkup:
#     """
#     Создает меню галереи с inline-кнопками.
    
#     Returns:
#         InlineKeyboardMarkup: Клавиатура меню галереи
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="🖼 Мои изображения",
#                 callback_data="gallery_my_images"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📤 Загрузить",
#                 callback_data="gallery_upload"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="🔍 Поиск",
#                 callback_data="gallery_search"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📁 Папки",
#                 callback_data="gallery_folders"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="⬅️ Назад",
#                 callback_data="back_to_main"
#             )
#         ]
#     ])

# LEGACY: Пустая функция для совместимости
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_gallery_menu() -> InlineKeyboardMarkup:
    """LEGACY: Заглушка для совместимости"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚧 Раздел в разработке",
                callback_data="main_menu"
            )
        ]
    ]) 