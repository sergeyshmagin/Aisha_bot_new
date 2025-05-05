# """Обработчики для анимации и улучшения фото в Telegram-боте Aisha."""
# from telebot.types import (
#     Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
#     ReplyKeyboardMarkup, KeyboardButton
# )
# from frontend_bot.handlers.general import bot
# from frontend_bot.services.state_manager import set_state, get_state
# from frontend_bot.utils.logger import get_logger
# from frontend_bot.keyboards.reply import (
#     photo_menu_keyboard, avatar_menu_keyboard, ai_photographer_keyboard,
#     my_avatars_keyboard
# )
# from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
# from frontend_bot.services.avatar_manager import get_avatars_index

# # Временное хранилище фото по user_id
# user_photos = {}

# # Временное хранилище фото для аватара по user_id
# # avatar_photos = defaultdict(list)
# # AVATAR_MIN_PHOTOS = 10

# # Хранилище аватаров пользователя (user_id: list of avatars)
# # user_avatars = defaultdict(list)
# # Временное состояние для ввода имени (user_id: True/False)
# # awaiting_avatar_name = set()
# # Временное хранилище для черновика аватара (user_id: dict)
# # draft_avatar = {}

# # Временное хранилище для message_id последнего сообщения-счётчика
# # avatar_counter_message_ids = {}

# # Временное хранилище: user_id -> avatar_id -> [message_id, ...]
# # user_photo_message_ids = {}

# logger = get_logger('photo_animate')

# # УДАЛЕНО: AVATAR_MIN_PHOTOS = 10

# def _save_photo(file_info, user_id: int, suffix: str) -> str:
#     """Сохраняет фото пользователя в папку storage и возвращает путь к файлу."""
#     # file_info: Информация о файле от Telegram API.
#     # user_id (int): ID пользователя.
#     # suffix (str): Суффикс для имени файла.
#     # Returns:
#     #   str: Путь к сохранённому файлу.
#     file_path = f"storage/{user_id}_{suffix}.jpg"
#     return file_path

# def gender_inline_keyboard():
#     keyboard = InlineKeyboardMarkup()
#     keyboard.row(
#         InlineKeyboardButton("👨 Мужской", callback_data="avatar_gender_man"),
#         InlineKeyboardButton("👩 Женский", callback_data="avatar_gender_woman"),
#         InlineKeyboardButton("⚧ Другое", callback_data="avatar_gender_other"),
#     )
#     return keyboard

# async def build_avatars_keyboard(avatars):
#     keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#     keyboard.add(KeyboardButton('📷 Создать аватар'))
#     for avatar in avatars:
#         if not isinstance(avatar, dict):
#             continue
#         title = avatar.get('title')
#         if title:  # Только если имя задано и не пустое
#             keyboard.add(KeyboardButton(str(title)))
#     keyboard.add(KeyboardButton('⬅️ Назад'))
#     return keyboard

# @bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
# async def photo_menu_entry(message: Message):
#     set_state(message.from_user.id, "photo_menu")
#     await bot.send_message(
#         message.chat.id,
#         "🖼 Работа с фото\n\nУлучшайте фото или создавайте ИИ-аватары.",
#         reply_markup=photo_menu_keyboard()
#     )

# @bot.message_handler(func=lambda m: m.text == "✨ Улучшить фото")
# async def enhance_photo_entry(message: Message):
#     await bot.send_message(
#         message.chat.id,
#         "Отправьте фото для улучшения качества ✨.",
#         reply_markup=ReplyKeyboardRemove()
#     )
#     set_state(message.from_user.id, 'photo_enhance')

# @bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
# async def ai_photographer_menu(message: Message):
#     set_state(message.from_user.id, "ai_photographer")
#     await bot.send_message(
#         message.chat.id,
#         "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
#         reply_markup=ai_photographer_keyboard()
#     )

# @bot.message_handler(func=lambda m: m.text == "🖼 Мои аватары")
# async def my_avatars_menu(message: Message):
#     set_state(message.from_user.id, "my_avatars")
#     user_id = message.from_user.id
#     avatars = get_avatars_index(user_id)
#     if not avatars:
#         await bot.send_message(
#             message.chat.id,
#             "Пока у вас нет аватаров. Создайте первый! 🚀",
#             reply_markup=my_avatars_keyboard()
#         )
#     else:
#         await bot.send_message(
#             message.chat.id,
#             "Меню аватаров:",
#             reply_markup=await build_avatars_keyboard(avatars)
#         )

# @bot.message_handler(func=lambda m: m.text == "🖼 Образы")
# async def gallery_menu(message: Message):
#     set_state(message.from_user.id, "gallery")
#     await bot.send_message(
#         message.chat.id,
#         "Галерея доступных образов и стилей скоро будет доступна.",
#         reply_markup=ai_photographer_keyboard()
#     )

# @bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
# async def universal_back_handler(message: Message):
#     user_id = message.from_user.id
#     state = get_state(user_id)
#     if state == "photo_menu":
#         set_state(user_id, "main_menu")
#         await bot.send_message(
#             message.chat.id,
#             "Главное меню. Выберите действие:",
#             reply_markup=main_menu_keyboard()
#         )
#     elif state == "ai_photographer":
#         set_state(user_id, "photo_menu")
#         await bot.send_message(
#             message.chat.id,
#             "🖼 Работа с фото\n\nУлучшайте фото или создавайте ИИ-аватары.",
#             reply_markup=photo_menu_keyboard()
#         )
#     elif state in ["my_avatars", "gallery"]:
#         set_state(user_id, "ai_photographer")
#         await bot.send_message(
#             message.chat.id,
#             "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
#             reply_markup=ai_photographer_keyboard()
#         )
#     else:
#         set_state(user_id, "main_menu")
#         await bot.send_message(
#             message.chat.id,
#             "Главное меню. Выберите действие:",
#             reply_markup=main_menu_keyboard()
#         )

# def delete_photo_keyboard(photo_idx):
#     keyboard = InlineKeyboardMarkup()
#     keyboard.add(InlineKeyboardButton("🗑️ Удалить", callback_data=f"avatar_del_photo_{photo_idx}"))
#     return keyboard

# # УДАЛЕНО: универсальный обработчик фото, чтобы не мешать FSM загрузки аватара
# # @bot.message_handler(content_types=['photo'])
# # async def handle_photo(message: Message) -> None:
# #     ...

# @bot.message_handler(func=lambda m: m.text == "🧑‍🎨 Аватары")
# async def avatar_menu(message):
#     """Открывает подменю 'Аватары'."""
#     await bot.send_message(
#         message.chat.id,
#         "Меню аватаров:",
#         reply_markup=avatar_menu_keyboard()
#     )

# def style_inline_keyboard():
#     keyboard = InlineKeyboardMarkup()
#     styles = [
#         ("Реалистичный", "realistic"),
#         ("Аниме", "anime"),
#         ("Мультфильм", "cartoon"),
#         ("Пиксель-арт", "pixel"),
#     ]
#     for label, value in styles:
#         keyboard.add(InlineKeyboardButton(label, callback_data=f"avatar_style_{value}"))
#     return keyboard

# # @bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_style_"))
# # async def handle_style_select(call):
# #     user_id = call.from_user.id
# #     style = call.data.replace("avatar_style_", "")
# #     avatar_id = get_current_avatar_id(user_id)
# #     update_avatar_fsm(user_id, avatar_id, style=style)
# #     set_state(user_id, "avatar_name_input")
# #     await bot.send_message(call.message.chat.id, "Введите имя для аватара:")

# # @bot.message_handler(func=lambda m: get_state(m.from_user.id) == "avatar_name_input")
# # async def handle_avatar_name_input(message):
# #     user_id = message.from_user.id
# #     avatar_id = get_current_avatar_id(user_id)
# #     name = message.text.strip()
# #     update_avatar_fsm(user_id, avatar_id, title=name)
# #     set_state(user_id, "my_avatars")
# #     await bot.send_message(
# #         message.chat.id,
# #         f"Аватар '{name}' готов к генерации!",
# #         reply_markup=my_avatars_keyboard()
# #     )

# # @bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_del_photo_"))
# # async def handle_delete_photo(call):
# #     user_id = call.from_user.id
# #     avatar_id = get_current_avatar_id(user_id)
# #     idx = int(call.data.replace("avatar_del_photo_", ""))
# #     data = load_avatar_fsm(user_id, avatar_id)
# #     photos = data.get('photos', [])
# #     if 0 <= idx < len(photos):
# #         import os
# #         try:
# #             os.remove(photos[idx])
# #         except Exception:
# #             pass
# #         del photos[idx]
# #         update_avatar_fsm(user_id, avatar_id, photos=photos)
# #         await bot.answer_callback_query(call.id, "Фото удалено!")
# #         # Удаляем сообщение-бота с инлайн-меню
# #         await bot.delete_message(call.message.chat.id, call.message.message_id)
# #         # Удаляем сообщение пользователя с фото
# #         try:
# #             user_msg_id = user_photo_message_ids[user_id][avatar_id][idx]
# #             await bot.delete_message(call.message.chat.id, user_msg_id)
# #             del user_photo_message_ids[user_id][avatar_id][idx]
# #         except Exception:
# #             pass
# #     else:
# #         await bot.answer_callback_query(call.id, "Ошибка удаления фото.")

# # @bot.message_handler(content_types=['photo'])
# # async def collect_avatar_photos(message):
# #     user_id = message.from_user.id
# #     if user_id not in avatar_photos:
# #         return  # Не в режиме сбора фото для аватара
# #     # Сохраняем фото
# #     file_info = await bot.get_file(message.photo[-1].file_id)
# #     file_path = f"storage/avatar_{user_id}_{len(avatar_photos[user_id])}.jpg"
# #     downloaded_file = await bot.download_file(file_info.file_path)
# #     async with aiofiles.open(file_path, "wb") as f:
# #         await f.write(downloaded_file)
# #     avatar_photos[user_id].append(file_path)
# #     if len(avatar_photos[user_id]) < AVATAR_MIN_PHOTOS:
# #         await bot.send_message(
# #             message.chat.id,
# #             f"Фото сохранено ({len(avatar_photos[user_id])}/{AVATAR_MIN_PHOTOS}). Пришлите ещё."
# #         )
# #     else:
# #         await bot.send_message(
# #             message.chat.id,
# #             "Достаточно фото! Теперь вы можете нажать 'Создать аватар' ещё раз для запуска генерации."
# #         )

# # @bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gender_"))
# # async def avatar_gender_callback(call):
# #     user_id = call.from_user.id
# #     gender = call.data.replace("avatar_gender_", "")
# #     gender_emoji = {"man": "👨", "woman": "👩", "other": "⚧"}.get(gender, "❓")
# #     draft_avatar[user_id] = {"gender": gender, "gender_emoji": gender_emoji, "photos": avatar_photos[user_id]}
# #     awaiting_avatar_name.add(user_id)
# #     await bot.send_message(call.message.chat.id, "Введите имя для аватара:")

# # @bot.message_handler(func=lambda m: m.from_user.id in awaiting_avatar_name)
# # async def avatar_name_input(message):
# #     user_id = message.from_user.id
# #     name = message.text.strip()
# #     # Генерируем уникальный id для аватара (можно заменить на uuid)
# #     avatar_id = f"{user_id}_{len(user_avatars[user_id]) + 1}"
# #     avatar = draft_avatar.pop(user_id)
# #     avatar.update({"id": avatar_id, "name": name})
# #     user_avatars[user_id].append(avatar)
# #     awaiting_avatar_name.discard(user_id)
# #     await bot.send_message(
# #         message.chat.id,
# #         f"Аватар '{name}' создан!",
# #         reply_markup=avatars_menu_keyboard(user_id, selected_id=avatar_id)
# #     )

# # Функция для показа меню аватаров (можно вызывать после создания/изменения/удаления)
# # def show_avatars_menu(user_id, chat_id, selected_id=None):
# #     text = (
# #         "\U0001F98B МОИ АВАТАРЫ\n\n"
# #         "Нажмите на имя аватара, чтобы выбрать его для генерации фото:"
# #     )
# #     bot.send_message(chat_id, text, reply_markup=avatars_menu_keyboard(user_id, selected_id=selected_id))
