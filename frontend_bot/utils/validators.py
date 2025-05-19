import functools
from frontend_bot.texts.common import ERROR_USER_AVATAR
from frontend_bot.services.state_utils import get_state
from frontend_bot.bot_instance import bot
from frontend_bot.repositories.user_repository import UserRepository
from database.config import AsyncSessionLocal
from frontend_bot.services.avatar_validator import validate_avatar_exists, validate_avatar_photos


def validate_user_avatar(handler):
    @functools.wraps(handler)
    async def wrapper(call_or_message, *args, **kwargs):
        user_id = getattr(getattr(call_or_message, "from_user", None), "id", None)
        avatar_id = None
        print(f"VALIDATOR: start, user_id={user_id}")
        
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(user_id)
            
            if not user:
                await bot.send_message(
                    call_or_message.message.chat.id,
                    "Ошибка: пользователь не найден"
                )
                if hasattr(call_or_message, "id"):
                    await bot.answer_callback_query(call_or_message.id)
                return
                
            from frontend_bot.services.avatar_manager import get_current_avatar_id
            avatar_id = get_current_avatar_id(user.id)
            
            if not avatar_id:
                await bot.send_message(
                    call_or_message.message.chat.id,
                    ERROR_USER_AVATAR
                )
                if hasattr(call_or_message, "id"):
                    await bot.answer_callback_query(call_or_message.id)
                return
                
            # Проверяем существование аватара
            is_valid, msg = await validate_avatar_exists(user.id, avatar_id, session)
            if not is_valid:
                await bot.send_message(
                    call_or_message.message.chat.id,
                    f"Ошибка: {msg}"
                )
                if hasattr(call_or_message, "id"):
                    await bot.answer_callback_query(call_or_message.id)
                return
                
            # Проверяем наличие фото
            is_valid, msg = await validate_avatar_photos(user.id, avatar_id, session)
            if not is_valid:
                await bot.send_message(
                    call_or_message.message.chat.id,
                    f"Ошибка: {msg}"
                )
                if hasattr(call_or_message, "id"):
                    await bot.answer_callback_query(call_or_message.id)
                return
                
        print(f"VALIDATOR: PASS, user_id={user_id}, avatar_id={avatar_id}")
        return await handler(call_or_message, *args, **kwargs)
        
    return wrapper


def validate_index(photos, idx):
    return 0 <= idx < len(photos)
