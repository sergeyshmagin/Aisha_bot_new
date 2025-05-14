"""Точка входа для запуска Telegram-бота."""

from frontend_bot.handlers.general import bot

# Импортируем хендлеры для фото и ИИ фотографа (регистрация)
import frontend_bot.handlers.avatar.fsm
import frontend_bot.handlers.avatar.photo_upload
import frontend_bot.handlers.avatar.gallery
import frontend_bot.handlers.avatar.confirm

if __name__ == "__main__":
    import asyncio

    asyncio.run(bot.polling())
