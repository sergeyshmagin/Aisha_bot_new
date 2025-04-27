"""Обработчики для анимации и улучшения фото в Telegram-боте Aisha."""
from frontend_bot.keyboards.emotion import emotion_keyboard
from frontend_bot.services.backend_client import (
    send_photo_for_enhancement
)
import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import (
    set_state, get_state, clear_state
)
import aiofiles
from frontend_bot.utils.logger import get_logger

# Временное хранилище фото по user_id
user_photos = {}

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
