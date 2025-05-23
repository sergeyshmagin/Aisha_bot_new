from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- LEGACY: меню бизнес-ассистента ---
# def get_business_menu() -> InlineKeyboardMarkup:
#     """
#     Создает меню бизнес-ассистента с inline-кнопками.
#     Returns:
#         InlineKeyboardMarkup: Клавиатура меню бизнес-ассистента
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="🎤 Обработать аудио",
#                 callback_data="business_audio"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="📝 Обработать текст",
#                 callback_data="business_text"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="⬅️ Назад",
#                 callback_data="back_to_main"
#             )
#         ]
#     ])
# --- END LEGACY --- 