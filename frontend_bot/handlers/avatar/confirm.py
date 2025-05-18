from frontend_bot.keyboards.common import confirm_keyboard
from frontend_bot.texts.avatar.texts import PHOTO_NAME_EMPTY, AVATAR_CONFIRM_TEXT
from frontend_bot.services.avatar_manager import get_current_avatar_id
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.bot_instance import bot
from frontend_bot.config import settings
from frontend_bot.services.fal_trainer import train_avatar
from frontend_bot.keyboards.reply import my_avatars_keyboard
from frontend_bot.texts.common import ERROR_FILE
from frontend_bot.utils.validators import validate_user_avatar
from frontend_bot.keyboards.avatar import avatar_confirm_keyboard
import logging
from frontend_bot.handlers.avatar.state import user_session
from frontend_bot.services.avatar_workflow import update_draft_avatar
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository

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
    telegram_id = call.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.send_message(call.message.chat.id, "Ошибка: пользователь не найден.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        avatar_id = get_current_avatar_id(uuid_user_id)
        mark_avatar_ready = __import__(
            "frontend_bot.services.avatar_manager", fromlist=["mark_avatar_ready"]
        ).mark_avatar_ready
        await mark_avatar_ready(uuid_user_id, avatar_id)
        finetune_comment = f"user_id={uuid_user_id};avatar_id={avatar_id}"
        if settings.FAL_TRAINING_TEST_MODE:
            logger.info(
                "FAL_TRAINING_TEST_MODE is ON: обучение не отправляется на fal.ai, "
                "используется фиктивный finetune_id."
            )
            finetune_id = "test-finetune-id"
        else:
            finetune_id = await train_avatar(
                uuid_user_id,
                avatar_id,
                data.get("title", ""),
                data.get("class_name", ""),
                photos,
                finetune_comment=finetune_comment,
                mode=settings.FAL_MODE,
                iterations=settings.FAL_ITERATIONS,
                priority=settings.FAL_PRIORITY,
                captioning=settings.FAL_CAPTIONING,
                trigger_word=settings.FAL_TRIGGER_WORD,
                lora_rank=settings.FAL_LORA_RANK,
                finetune_type=settings.FAL_FINETUNE_TYPE,
                webhook_url=settings.FAL_WEBHOOK_URL,
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
async def handle_avatar_type(call, db: AsyncSession = None):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(call.message.chat.id, "Ошибка: не найден аватар.")
        await bot.answer_callback_query(call.id)
        return
    gender = "man" if call.data == "avatar_type_man" else "woman"
    session = db
    if session is None:
        from frontend_bot.database import get_async_session
        async with get_async_session() as session:
            await update_draft_avatar(user_id, session, {"avatar_data": {"gender": gender}})
    else:
        await update_draft_avatar(user_id, session, {"avatar_data": {"gender": gender}})
    await set_state(user_id, "avatar_enter_name", session)
    await bot.send_message(call.message.chat.id, "Введите имя для вашего аватара:")
    await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text not in ["⬅️ Назад", "Отмена"])
async def handle_avatar_name_input(message, db: AsyncSession = None):
    user_id = message.from_user.id
    state = await get_state(user_id, db)
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
        session = db
        if session is None:
            from frontend_bot.database import get_async_session
            async with get_async_session() as session:
                await update_draft_avatar(user_id, session, {"avatar_data": {"title": name}})
        else:
            await update_draft_avatar(user_id, session, {"avatar_data": {"title": name}})
        from frontend_bot.services.avatar_manager import get_avatars_index, load_avatar_fsm
        from frontend_bot.handlers.avatar.gallery import send_avatar_card
        mode = user_session.get(user_id, {}).get("edit_mode", "create")
        # После действия очищаем edit_mode
        user_session.get(user_id, {}).pop("edit_mode", None)
        if mode == "create":
            photos = await get_avatar_photos_from_db(user_id, avatar_id)
            await set_state(user_id, "avatar_confirm", session)
            gender = data.get("gender", "-")
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
            async with AsyncSessionLocal() as session:
                avatars = await get_avatars_index(user_id, session)
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
    await set_state(user_id, "avatar_enter_name", session)
    await bot.send_message(call.message.chat.id, "Введите новое имя для аватара:")
    await bot.answer_callback_query(call.id)


# Остальные обработчики (handle_avatar_confirm_edit,
# handle_avatar_cancel, handle_create_avatar) переносить по аналогии...
