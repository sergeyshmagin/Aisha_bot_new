import logging
from frontend_bot.bot_instance import bot
from frontend_bot.services.state_utils import get_state_pg, set_state_pg
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import (
    photo_menu_keyboard,
    ai_photographer_keyboard,
    my_avatars_keyboard,
    photo_enhance_keyboard,
    transcribe_keyboard,
)
from frontend_bot.services.avatar_manager import get_avatars_index
from frontend_bot.services.avatar_workflow import cleanup_state
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
async def handle_back(message):
    """Обработчик возврата в предыдущее меню."""
    logger.info(f"handle_back: message.text={message.text!r}, user_id={message.from_user.id}")
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await message.reply("Пользователь не найден. Пожалуйста, /start.")
                return
            uuid_user_id = user.id
            state = await get_state_pg(uuid_user_id, session)
            if state == "photo_enhance":
                await handle_photo_enhance_back(message)
            elif state == "transcribe":
                await handle_transcribe_back(message)
            else:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
                await bot.send_message(
                    message.chat.id,
                    "Выберите действие:",
                    reply_markup=main_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in handle_back: {e}")
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
            try:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
            except Exception as state_error:
                logger.error(f"Error setting state in handle_back: {state_error}")

@bot.message_handler(func=lambda message: message.text == "Отмена")
async def handle_cancel(message):
    """Обработчик отмены текущего действия."""
    logger.info(f"handle_cancel: message.text={message.text!r}, user_id={message.from_user.id}")
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await message.reply("Пользователь не найден. Пожалуйста, /start.")
                return
            uuid_user_id = user.id
            state = await get_state_pg(uuid_user_id, session)
            # Обработка отмены для аватара
            if state and state.startswith("avatar_"):
                await cleanup_state(uuid_user_id, session)
                await session.commit()
                await bot.send_message(
                    message.chat.id,
                    "Создание аватара отменено.",
                    reply_markup=main_menu_keyboard()
                )
                return
            # Обработка отмены для других состояний
            if state == "photo_enhance":
                await handle_photo_enhance_back(message)
            elif state == "transcribe":
                await handle_transcribe_back(message)
            else:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
                await bot.send_message(
                    message.chat.id,
                    "Действие отменено.",
                    reply_markup=main_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in handle_cancel: {e}")
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка при отмене действия. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
            try:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
            except Exception as state_error:
                logger.error(f"Error setting state in handle_cancel: {state_error}")

async def handle_photo_enhance_back(message):
    """Обработчик возврата в меню улучшения фото."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await message.reply("Пользователь не найден. Пожалуйста, /start.")
                return
            uuid_user_id = user.id
            await set_state_pg(uuid_user_id, "main_menu", session)
            await session.commit()
            await bot.send_message(
                message.chat.id,
                "Выберите действие:",
                reply_markup=photo_enhance_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in handle_photo_enhance_back: {e}")
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
            try:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
            except Exception as state_error:
                logger.error(f"Error setting state in handle_photo_enhance_back: {state_error}")

async def handle_transcribe_back(message):
    """Обработчик возврата в меню транскрибации."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await message.reply("Пользователь не найден. Пожалуйста, /start.")
                return
            uuid_user_id = user.id
            await set_state_pg(uuid_user_id, "main_menu", session)
            await session.commit()
            await bot.send_message(
                message.chat.id,
                "Выберите действие:",
                reply_markup=transcribe_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in handle_transcribe_back: {e}")
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
            try:
                await set_state_pg(uuid_user_id, "main_menu", session)
                await session.commit()
            except Exception as state_error:
                logger.error(f"Error setting state in handle_transcribe_back: {state_error}")
