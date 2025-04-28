"""Точка входа для запуска Telegram-бота."""

from frontend_bot.handlers.general import bot
import frontend_bot.handlers.transcribe
import frontend_bot.handlers.photo_animate
import frontend_bot.handlers.gallery


if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.polling())
