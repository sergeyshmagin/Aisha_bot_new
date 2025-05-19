"""
Обработчики создания аватара.
"""

import logging
from frontend_bot.bot_instance import bot
from frontend_bot.services.state_utils import set_state
from frontend_bot.services.avatar_workflow import create_draft_avatar
from frontend_bot.services.avatar_validator import validate_avatar_exists
from frontend_bot.keyboards.avatar import avatar_photo_keyboard
from frontend_bot.texts.avatar.texts import PROMPT_PHOTO_UPLOAD
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.handlers.avatar.navigation import start_avatar_wizard

logger = logging.getLogger(__name__)

@bot.message_handler(commands=["create_avatar"])
async def handle_create_avatar(message):
    """
    Обрабатывает команду создания аватара.
    
    Args:
        message (Message): Объект сообщения
    """
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        # Получаем пользователя
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(user_id)
        
        if not user:
            await bot.send_message(
                message.chat.id,
                "Ошибка: пользователь не найден"
            )
            return
            
        try:
            await start_avatar_wizard(bot, message.chat.id, user.id, session)
        except Exception as e:
            logger.exception("Ошибка при создании аватара: %s", e)
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка при создании аватара. Попробуйте позже."
            ) 