from frontend_bot.keyboards.common import confirm_keyboard
from frontend_bot.texts.avatar.texts import PHOTO_NAME_EMPTY, AVATAR_CONFIRM_TEXT
from frontend_bot.services.avatar_manager import update_avatar_fsm, load_avatar_fsm, get_current_avatar_id
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.bot_instance import bot
from frontend_bot.config import (
    FAL_MODE,
    FAL_ITERATIONS,
    FAL_PRIORITY,
    FAL_CAPTIONING,
    FAL_TRIGGER_WORD,
    FAL_LORA_RANK,
    FAL_FINETUNE_TYPE,
    FAL_WEBHOOK_URL,
    FAL_TRAINING_TEST_MODE,
)
from frontend_bot.services.fal_trainer import train_avatar
from frontend_bot.keyboards.reply import my_avatars_keyboard
from frontend_bot.texts.common import ERROR_FILE
from frontend_bot.utils.validators import validate_user_avatar
from frontend_bot.keyboards.avatar import avatar_confirm_keyboard
import logging
from frontend_bot.handlers.transcribe import user_states
from frontend_bot.handlers.avatar.state import user_session

print("CONFIRM HANDLERS LOADED")
# Модуль подтверждения и управления аватаром
# Перенести сюда handle_avatar_confirm_yes,
# handle_avatar_confirm_edit, handle_avatar_cancel, handle_create_avatar
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_manager, utils, config и т.д.

logger = logging.getLogger(__name__)

MENU_COMMANDS = [
    "📷 Создать аватар",
    "👁 Просмотреть аватары",
    "⬅️ Назад",
    # Добавьте другие кнопки, если есть
]

CANCEL_COMMANDS = [
    "⬅️ Назад",
    "Отмена",
]
ALL_MENU_COMMANDS = [
    "📷 Создать аватар",
    "👁 Просмотреть аватары",
    "🧑‍🎨 ИИ фотограф",
    "✨ Улучшить фото",
    "🖼 Мои аватары",
    "🖼 Работа с фото",
    "🖼 Образы",
    # Добавьте другие кнопки, если есть
]


@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_yes")
@validate_user_avatar
async def handle_avatar_confirm_yes(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    from frontend_bot.services.avatar_manager import load_avatar_fsm

    mark_avatar_ready = __import__(
        "frontend_bot.services.avatar_manager", fromlist=["mark_avatar_ready"]
    ).mark_avatar_ready
    await mark_avatar_ready(user_id, avatar_id)
    data = await load_avatar_fsm(user_id, avatar_id)
    photos = [p["path"] if isinstance(p, dict) else p for p in data.get("photos", [])]
    finetune_comment = f"user_id={user_id};avatar_id={avatar_id}"
    if FAL_TRAINING_TEST_MODE:
        logger.info(
            "FAL_TRAINING_TEST_MODE is ON: обучение не отправляется на fal.ai, "
            "используется фиктивный finetune_id."
        )
        finetune_id = "test-finetune-id"
    else:
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
            webhook_url=FAL_WEBHOOK_URL,
        )
    if not finetune_id:
        await bot.send_message(call.message.chat.id, ERROR_FILE)
        await bot.answer_callback_query(call.id)
        return
    final_text = (
        "✨✨ <b>СОЗДАНИЕ АВАТАРА...</b> ✨✨\n\n"
        "Это займёт примерно 15 минут.\n"
        "Когда аватар будет готов, вы получите уведомление прямо здесь.\n\n"
        "Пожалуйста, ожидайте — магия уже началась! 🦋"
    )
    await bot.send_message(call.message.chat.id, final_text, parse_mode="HTML")
    await bot.send_message(
        call.message.chat.id,
        "🦋 Вы вернулись в меню аватаров.",
        reply_markup=my_avatars_keyboard(),
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data in ["avatar_type_man", "avatar_type_woman"]
)
async def handle_avatar_type(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(call.message.chat.id, "Ошибка: не найден аватар.")
        await bot.answer_callback_query(call.id)
        return
    gender = "man" if call.data == "avatar_type_man" else "woman"
    from frontend_bot.services.avatar_manager import update_avatar_fsm
    from frontend_bot.services.state_utils import set_state

    await update_avatar_fsm(user_id, avatar_id, gender=gender)
    await set_state(user_id, "avatar_enter_name")
    await bot.send_message(call.message.chat.id, "Введите имя для вашего аватара:")
    await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text not in ["⬅️ Назад", "Отмена"])
async def handle_avatar_name_input(message):
    user_id = message.from_user.id
    state = await get_state(user_id)
    if state != "avatar_enter_name":
        return  # Не обрабатываем, если не то состояние
    name = message.text.strip()
    if not name:
        await bot.send_message(message.chat.id, PHOTO_NAME_EMPTY)
        return
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(message.chat.id, "Ошибка: не найден аватар.")
        return
    try:
        await update_avatar_fsm(user_id, avatar_id, title=name)
        from frontend_bot.services.avatar_manager import get_avatars_index, load_avatar_fsm
        from frontend_bot.handlers.avatar.gallery import send_avatar_card
        mode = user_session.get(user_id, {}).get("edit_mode", "create")
        # После действия очищаем edit_mode
        user_session.get(user_id, {}).pop("edit_mode", None)
        if mode == "create":
            data = await load_avatar_fsm(user_id, avatar_id)
            await set_state(user_id, "avatar_confirm")
            gender = data.get("gender", "-")
            photos = data.get("photos", [])
            gender_str = "Мужчина" if gender == "man" else ("Женщина" if gender == "woman" else "-")
            gender_emoji = "👨‍🦰" if gender == "man" else ("👩‍🦰" if gender == "woman" else "❓")
            price = 150
            balance = 250
            text = AVATAR_CONFIRM_TEXT.format(
                title=name,
                gender=gender_str,
                gender_emoji=gender_emoji,
                photo_count=len(photos),
                price=price,
                balance=balance,
            )
            await bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=avatar_confirm_keyboard(),
            )
        else:
            avatars = await get_avatars_index(user_id)
            idx = next((i for i, a in enumerate(avatars) if a["avatar_id"] == avatar_id), 0)
            await send_avatar_card(message.chat.id, user_id, avatars, idx)
    except Exception as e:
        logger.exception("[handle_avatar_name_input] Необработанная ошибка: %s", e)
        await bot.send_message(
            message.chat.id, "Произошла ошибка. Попробуйте ещё раз."
        )


@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_edit")
async def handle_avatar_confirm_edit(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(call.message.chat.id, "Ошибка: не найден аватар.")
        await bot.answer_callback_query(call.id)
        return
    await set_state(user_id, "avatar_enter_name")
    await bot.send_message(call.message.chat.id, "Введите новое имя для аватара:")
    await bot.answer_callback_query(call.id)


# Остальные обработчики (handle_avatar_confirm_edit,
# handle_avatar_cancel, handle_create_avatar) переносить по аналогии...
