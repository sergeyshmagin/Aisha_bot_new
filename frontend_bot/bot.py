"""Точка входа для запуска Telegram-бота."""

from frontend_bot.handlers.general import bot
import frontend_bot.handlers.transcribe
import frontend_bot.handlers.photo_animate
import frontend_bot.handlers.gallery
import frontend_bot.handlers.avatar_fsm
import frontend_bot.handlers.photo_tools
import frontend_bot.handlers.universal_back


if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.polling())
