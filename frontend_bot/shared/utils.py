import logging
from typing import Optional
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from io import BytesIO


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


async def send_and_track(bot, user_session, user_id, chat_id, *args, **kwargs):
    """
    Отправляет сообщение и сохраняет его ID в сессии пользователя.
    
    Args:
        bot: Экземпляр бота
        user_session: Словарь сессий пользователей
        user_id: ID пользователя
        chat_id: ID чата
        *args: Аргументы для bot.send_message
        **kwargs: Именованные аргументы для bot.send_message
        
    Returns:
        Message: Объект сообщения
    """
    msg = await bot.send_message(chat_id, *args, **kwargs)
    if user_id not in user_session:
        user_session[user_id] = {"wizard_message_ids": []}
    user_session[user_id]["wizard_message_ids"].append(msg.message_id)
    return msg


async def send_photo_validation_error(bot, chat_id, photo_bytes, error_text: str):
    """
    Отправляет сообщение с ошибкой валидации фото и inline-кнопкой 'Понятно'.
    Args:
        bot: экземпляр бота
        chat_id: ID чата
        photo_bytes: байты фото
        error_text: текст ошибки
    Returns:
        Message: отправленное сообщение
    """
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
    text = (
        f"⚠️ Фото не принято: {error_text}\n"
        "📸 Совет: используйте чёткие фото без фильтров."
    )
    return await bot.send_photo(
        chat_id, BytesIO(photo_bytes), caption=text, reply_markup=markup
    )
