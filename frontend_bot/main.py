import logging
import asyncio
from frontend_bot.bot_instance import bot

# Импорт специфичных хендлеров (первыми)
import frontend_bot.handlers.transcribe_audio
import frontend_bot.handlers.transcribe
import frontend_bot.handlers.transcribe_history
import frontend_bot.handlers.transcribe_protocol
import frontend_bot.handlers.avatar.fsm
import frontend_bot.handlers.avatar.photo_upload
import frontend_bot.handlers.avatar.gallery
import frontend_bot.handlers.avatar.confirm
import frontend_bot.handlers.image_gallery
import frontend_bot.handlers.start

# Универсальные хендлеры (последними)
import frontend_bot.handlers.universal_back
import frontend_bot.handlers.general

print("=== BOT MAIN STARTED ===")
logging.basicConfig(level=logging.INFO)
logging.info("=== BOT MAIN STARTED ===")

if __name__ == "__main__":
    print("=== POLLING START ===")
    logging.info("=== POLLING START ===")
    asyncio.run(bot.polling())
