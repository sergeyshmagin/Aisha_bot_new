import logging
import asyncio
from frontend_bot.bot_instance import bot

# Импорт всех хендлеров для регистрации
import frontend_bot.handlers.general
import frontend_bot.handlers.universal_back
import frontend_bot.handlers.image_gallery
import frontend_bot.handlers.start
import frontend_bot.handlers.avatar.fsm
import frontend_bot.handlers.avatar.photo_upload
import frontend_bot.handlers.transcribe_audio
import frontend_bot.handlers.transcribe_history
import frontend_bot.handlers.transcribe_protocol

# Универсальные хендлеры — СТРОГО В КОНЦЕ!
import frontend_bot.handlers.avatar.gallery
import frontend_bot.handlers.avatar.confirm

print("=== BOT MAIN STARTED ===")
logging.basicConfig(level=logging.INFO)
logging.info("=== BOT MAIN STARTED ===")


if __name__ == "__main__":
    print("=== POLLING START ===")
    logging.info("=== POLLING START ===")
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # Если event loop уже запущен (Jupyter, PyCharm и др.)
            loop.create_task(bot.polling())
        else:
            loop.run_until_complete(bot.polling())
    except RuntimeError:
        # Нет активного event loop (обычный запуск)
        asyncio.run(bot.polling())

