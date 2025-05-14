import logging
from typing import Optional


async def clear_old_wizard_messages(
    bot,
    user_session,
    chat_id: int,
    user_id: int,
    keep_msg_id: Optional[int] = None,
) -> None:
    """
    Удаляет все сообщения визарда, кроме указанного (актуального).
    Логирует исключения с traceback.
    """
    if user_id not in user_session:
        return
    msg_ids = user_session[user_id]["wizard_message_ids"]
    for mid in msg_ids:
        if keep_msg_id is not None and mid == keep_msg_id:
            continue
        try:
            await bot.delete_message(chat_id, mid)
        except Exception as e:
            logging.exception(
                "[clear_old_wizard_messages] Exception при удалении сообщения "
                f"{mid}: {e}"
            )
    # Оставляем только актуальный message_id
    if keep_msg_id:
        user_session[user_id]["wizard_message_ids"] = [keep_msg_id]
    else:
        user_session[user_id]["wizard_message_ids"] = []


async def delete_last_error_message(bot, user_session, user_id, chat_id):
    if user_id not in user_session:
        return
    old_err = user_session[user_id]["last_error_msg"]
    if old_err:
        try:
            await bot.delete_message(chat_id, old_err)
        except Exception:
            pass
        user_session[user_id]["last_error_msg"] = None


async def delete_last_info_message(bot, user_session, user_id, chat_id):
    if user_id not in user_session:
        return
    msg_id = user_session[user_id].get("last_info_msg_id")
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        user_session[user_id]["last_info_msg_id"] = None
