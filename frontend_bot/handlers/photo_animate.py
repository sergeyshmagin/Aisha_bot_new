"""Обработчики для анимации и улучшения фото в Telegram-боте Aisha."""
from frontend_bot.keyboards.emotion import emotion_keyboard
from frontend_bot.services.backend_client import (
    send_photo_for_enhancement
)
import os
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import (
    set_state, get_state, clear_state
)
import aiofiles
from frontend_bot.utils.logger import get_logger
from frontend_bot.keyboards.reply import photo_menu_keyboard, avatar_menu_keyboard
from collections import defaultdict

# Временное хранилище фото по user_id
user_photos = {}

# Временное хранилище фото для аватара по user_id
avatar_photos = defaultdict(list)
AVATAR_MIN_PHOTOS = 10

# Хранилище аватаров пользователя (user_id: list of avatars)
user_avatars = defaultdict(list)
# Временное состояние для ввода имени (user_id: True/False)
awaiting_avatar_name = set()
# Временное хранилище для черновика аватара (user_id: dict)
draft_avatar = {}

logger = get_logger('photo_animate')

def _save_photo(file_info, user_id: int, suffix: str) -> str:
    """Сохраняет фото пользователя в папку storage и возвращает путь к файлу."""
    # file_info: Информация о файле от Telegram API.
    # user_id (int): ID пользователя.
    # suffix (str): Суффикс для имени файла.
    # Returns:
    #   str: Путь к сохранённому файлу.
    file_path = f"storage/{user_id}_{suffix}.jpg"
    return file_path

def gender_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("👨 Мужской", callback_data="avatar_gender_man"),
        InlineKeyboardButton("👩 Женский", callback_data="avatar_gender_woman"),
        InlineKeyboardButton("⚧ Другое", callback_data="avatar_gender_other"),
    )
    return keyboard

def avatars_menu_keyboard(user_id, selected_id=None):
    keyboard = InlineKeyboardMarkup()
    for avatar in user_avatars[user_id]:
        row = []
        name_btn = InlineKeyboardButton(
            ("✅ " if avatar["id"] == selected_id else "") + avatar["name"],
            callback_data=f"avatar_select_{avatar['id']}"
        )
        gender_btn = InlineKeyboardButton(f"пол {avatar['gender_emoji']}", callback_data=f"avatar_genderedit_{avatar['id']}")
        edit_btn = InlineKeyboardButton("✏️ изменить", callback_data=f"avatar_edit_{avatar['id']}")
        del_btn = InlineKeyboardButton("🗑 удалить", callback_data=f"avatar_del_{avatar['id']}")
        row.extend([gender_btn, edit_btn, del_btn])
        keyboard.add(name_btn)
        keyboard.row(*row)
    return keyboard

@bot.message_handler(func=lambda m: m.text == "✨ Улучшить фото")
async def ask_for_photo_enhance(message: Message) -> None:
    """Обработчик кнопки '✨ Улучшить фото'."""
    logger.info(
        f"Пользователь {message.from_user.id} выбрал режим: photo_enhance"
    )
    set_state(message.from_user.id, 'photo_enhance')
    await bot.send_message(
        message.chat.id,
        "📤 Пришли фото, которое нужно улучшить через GFPGAN."
    )

@bot.message_handler(content_types=['photo'])
async def handle_photo(message: Message) -> None:
    """Обрабатывает полученное фото: улучшение или анимация."""
    user_id = message.from_user.id
    state = get_state(user_id)
    logger.debug(f"Получено фото от {user_id}, state={state}")
    if state == 'photo_enhance':
        # Режим улучшения фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = _save_photo(file_info, user_id, 'photo_enhance')
        downloaded_file = await bot.download_file(file_info.file_path)
        os.makedirs("storage", exist_ok=True)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(downloaded_file)
        clear_state(user_id)
        await bot.send_message(
            message.chat.id,
            "✨ Улучшаю фото, подожди немного..."
        )
        try:
            enhanced_path = await send_photo_for_enhancement(file_path)
            async with aiofiles.open(enhanced_path, "rb") as f:
                await bot.send_photo(message.chat.id, await f.read())
        except Exception as e:
            logger.error(
                f"Ошибка при улучшении фото для пользователя {user_id}: {e}"
            )
            await bot.send_message(
                message.chat.id,
                "❌ Ошибка при улучшении фото."
            )
        return
    # Обычный режим (анимация)
    # самое большое по качеству
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = _save_photo(file_info, user_id, 'photo')
    downloaded_file = await bot.download_file(file_info.file_path)
    os.makedirs("storage", exist_ok=True)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(downloaded_file)
    user_photos[user_id] = file_path
    await bot.send_message(
        message.chat.id,
        "📸 Фото получено! Выберите стиль оживления:",
        reply_markup=emotion_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "↩️ В меню")
async def back_to_photo_menu(message):
    await bot.send_message(
        message.chat.id,
        "Вы вернулись в меню 'Работа с фото'.",
        reply_markup=photo_menu_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 Аватары")
async def avatar_menu(message):
    """Открывает подменю 'Аватары'."""
    await bot.send_message(
        message.chat.id,
        "Меню аватаров:",
        reply_markup=avatar_menu_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 Создать аватар")
async def start_avatar_creation(message):
    """Запускает режим сбора фото для создания аватара."""
    avatar_photos[message.from_user.id] = []
    await bot.send_message(
        message.chat.id,
        f"Пожалуйста, пришлите не менее {AVATAR_MIN_PHOTOS} своих фото для создания аватара. После загрузки каждого фото отправьте следующее."
    )

@bot.message_handler(content_types=['photo'])
async def collect_avatar_photos(message):
    user_id = message.from_user.id
    if user_id not in avatar_photos:
        return  # Не в режиме сбора фото для аватара
    # Сохраняем фото
    file_info = await bot.get_file(message.photo[-1].file_id)
    file_path = f"storage/avatar_{user_id}_{len(avatar_photos[user_id])}.jpg"
    downloaded_file = await bot.download_file(file_info.file_path)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(downloaded_file)
    avatar_photos[user_id].append(file_path)
    if len(avatar_photos[user_id]) < AVATAR_MIN_PHOTOS:
        await bot.send_message(
            message.chat.id,
            f"Фото сохранено ({len(avatar_photos[user_id])}/{AVATAR_MIN_PHOTOS}). Пришлите ещё."
        )
    else:
        await bot.send_message(
            message.chat.id,
            "Достаточно фото! Теперь вы можете нажать 'Создать аватар' ещё раз для запуска генерации."
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gender_"))
async def avatar_gender_callback(call):
    user_id = call.from_user.id
    gender = call.data.replace("avatar_gender_", "")
    gender_emoji = {"man": "👨", "woman": "👩", "other": "⚧"}.get(gender, "❓")
    draft_avatar[user_id] = {"gender": gender, "gender_emoji": gender_emoji, "photos": avatar_photos[user_id]}
    awaiting_avatar_name.add(user_id)
    await bot.send_message(call.message.chat.id, "Введите имя для аватара:")

@bot.message_handler(func=lambda m: m.from_user.id in awaiting_avatar_name)
async def avatar_name_input(message):
    user_id = message.from_user.id
    name = message.text.strip()
    # Генерируем уникальный id для аватара (можно заменить на uuid)
    avatar_id = f"{user_id}_{len(user_avatars[user_id]) + 1}"
    avatar = draft_avatar.pop(user_id)
    avatar.update({"id": avatar_id, "name": name})
    user_avatars[user_id].append(avatar)
    awaiting_avatar_name.discard(user_id)
    await bot.send_message(
        message.chat.id,
        f"Аватар '{name}' создан!",
        reply_markup=avatars_menu_keyboard(user_id, selected_id=avatar_id)
    )

# Функция для показа меню аватаров (можно вызывать после создания/изменения/удаления)
def show_avatars_menu(user_id, chat_id, selected_id=None):
    text = "\U0001F98B МОИ АВАТАРЫ\n\nНажмите на имя аватара, чтобы выбрать его для генерации фото:"
    bot.send_message(chat_id, text, reply_markup=avatars_menu_keyboard(user_id, selected_id=selected_id))
