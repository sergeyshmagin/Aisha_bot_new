import logging
import asyncio
from frontend_bot.bot import bot

# Импорт всех хендлеров для регистрации
import frontend_bot.handlers.transcribe
import frontend_bot.handlers.universal_back
import frontend_bot.handlers.image_gallery
import frontend_bot.handlers.general
import frontend_bot.handlers.start
import frontend_bot.handlers.photo_animate

# Импорт avatar-хендлеров до универсального
import frontend_bot.handlers.avatar.fsm
import frontend_bot.handlers.avatar.photo_upload
import frontend_bot.handlers.avatar.gallery
import frontend_bot.handlers.avatar.confirm

# Новые импорты для новых модулей хендлеров
import frontend_bot.handlers.transcribe_audio
import frontend_bot.handlers.transcribe_history
import frontend_bot.handlers.transcribe_protocol

print("=== BOT MAIN STARTED ===")
logging.basicConfig(level=logging.INFO)
logging.info("=== BOT MAIN STARTED ===")

if __name__ == "__main__":
    print("=== POLLING START ===")
    logging.info("=== POLLING START ===")
    asyncio.run(bot.polling())
