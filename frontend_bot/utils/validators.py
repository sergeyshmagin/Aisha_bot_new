import functools
from frontend_bot.texts.common import ERROR_USER_AVATAR


def validate_user_avatar(handler):
    @functools.wraps(handler)
    async def wrapper(call_or_message, *args, **kwargs):
        user_id = getattr(getattr(call_or_message, "from_user", None), "id", None)
        avatar_id = None
        if hasattr(call_or_message, "data") or hasattr(call_or_message, "text"):
            # callback или message
            from frontend_bot.services.state_manager import get_current_avatar_id

            avatar_id = get_current_avatar_id(user_id)
        if not isinstance(user_id, int) or not avatar_id:
            await call_or_message.bot.send_message(
                call_or_message.chat.id, ERROR_USER_AVATAR
            )
            if hasattr(call_or_message, "id"):
                await call_or_message.bot.answer_callback_query(call_or_message.id)
            return
        return await handler(call_or_message, *args, **kwargs)

    return wrapper


def validate_index(photos, idx):
    return 0 <= idx < len(photos)
