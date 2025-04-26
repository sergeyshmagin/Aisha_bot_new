from frontend_bot.keyboards.emotion import emotion_keyboard
from frontend_bot.services.backend_client import send_photo_for_animation, send_photo_for_enhancement
import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import set_state, get_state, clear_state

# Временное хранилище фото по user_id
user_photos = {}
user_enhance_mode = set()
user_states = {}

@bot.message_handler(func=lambda m: m.text == "✨ Улучшить фото")
async def ask_for_photo_enhance(message: Message):
    set_state(message.from_user.id, 'photo_enhance')
    await bot.send_message(message.chat.id, "📤 Пришли фото, которое нужно улучшить через GFPGAN.")

@bot.message_handler(content_types=['photo'])
async def handle_photo(message: Message):
    user_id = message.from_user.id
    if get_state(user_id) == 'photo_enhance':
        # Режим улучшения фото
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = f"storage/{user_id}_photo_enhance.jpg"
        downloaded_file = await bot.download_file(file_info.file_path)
        os.makedirs("storage", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(downloaded_file)
        clear_state(user_id)
        await bot.send_message(message.chat.id, "✨ Улучшаю фото, подожди немного...")
        try:
            enhanced_path = await send_photo_for_enhancement(file_path)
            with open(enhanced_path, "rb") as f:
                await bot.send_photo(message.chat.id, f)
        except Exception as e:
            await bot.send_message(message.chat.id, "❌ Ошибка при улучшении фото.")
            raise e
        return
    # Обычный режим (анимация)
    photo = message.photo[-1]  # самое большое по качеству
    file_info = await bot.get_file(photo.file_id)
    file_path = f"storage/{user_id}_photo.jpg"
    downloaded_file = await bot.download_file(file_info.file_path)
    os.makedirs("storage", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(downloaded_file)
    user_photos[user_id] = file_path
    await bot.send_message(
        message.chat.id,
        "📸 Фото получено! Выберите стиль оживления:",
        reply_markup=emotion_keyboard()
    )
