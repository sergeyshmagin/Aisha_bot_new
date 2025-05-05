# Модуль подтверждения и управления аватаром
# Перенести сюда handle_avatar_confirm_yes, handle_avatar_confirm_edit, handle_avatar_cancel, handle_create_avatar
# Импортировать необходимые зависимости и утилиты из avatar_manager, state_manager, utils, config и т.д.

import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.bot import bot
from frontend_bot.services.avatar_manager import load_avatar_fsm, clear_avatar_fsm
from frontend_bot.services.state_manager import get_current_avatar_id, set_state, clear_state
from frontend_bot.handlers.avatar.utils import reset_avatar_fsm
from frontend_bot.config import FAL_MODE, FAL_ITERATIONS, FAL_PRIORITY, FAL_CAPTIONING, FAL_TRIGGER_WORD, FAL_LORA_RANK, FAL_FINETUNE_TYPE, FAL_WEBHOOK_URL
from frontend_bot.services.fal_trainer import train_avatar
from frontend_bot.keyboards.reply import my_avatars_keyboard
from frontend_bot.handlers.avatar.state import user_session, user_gallery

logger = logging.getLogger(__name__)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_yes")
async def handle_avatar_confirm_yes(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    from frontend_bot.services.avatar_manager import load_avatar_fsm
    mark_avatar_ready = __import__(
        'frontend_bot.services.avatar_manager', fromlist=['mark_avatar_ready']
    ).mark_avatar_ready
    mark_avatar_ready(user_id, avatar_id)
    data = load_avatar_fsm(user_id, avatar_id)
    photos = [p["path"] if isinstance(p, dict) else p for p in data.get("photos", [])]
    finetune_comment = f"user_id={user_id};avatar_id={avatar_id}"
    finetune_id = await train_avatar(
        user_id,
        avatar_id,
        data.get("title", ""),
        data.get("class_name", ""),
        photos,
        finetune_comment=finetune_comment,
        mode=FAL_MODE,
        iterations=FAL_ITERATIONS,
        priority=FAL_PRIORITY,
        captioning=FAL_CAPTIONING,
        trigger_word=FAL_TRIGGER_WORD,
        lora_rank=FAL_LORA_RANK,
        finetune_type=FAL_FINETUNE_TYPE,
        webhook_url=FAL_WEBHOOK_URL
    )
    if not finetune_id:
        await bot.send_message(
            call.message.chat.id,
            "❌ Ошибка обучения аватара. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку."
        )
        await bot.answer_callback_query(call.id)
        return
    final_text = (
        "✨✨ <b>СОЗДАНИЕ АВАТАРА...</b> ✨✨\n\n"
        "Это займёт несколько минут.\n"
        "Когда аватар будет готов, вы получите уведомление прямо здесь.\n\n"
        "Пожалуйста, ожидайте — магия уже началась! 🦋"
    )
    await bot.send_message(
        call.message.chat.id,
        final_text,
        parse_mode="HTML"
    )
    await bot.send_message(
        call.message.chat.id,
        "🦋 Вы вернулись в меню аватаров.",
        reply_markup=my_avatars_keyboard()
    )
    await bot.answer_callback_query(call.id)

# Остальные обработчики (handle_avatar_confirm_edit, handle_avatar_cancel, handle_create_avatar) переносить по аналогии... 