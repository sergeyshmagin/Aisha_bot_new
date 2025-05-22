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
from frontend_bot.services.avatar_workflow import update_draft_avatar, finalize_draft_avatar
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.services.avatar_validator import validate_avatar_exists, validate_avatar_photos, validate_avatar_state
from frontend_bot.services.avatar_fsm_service import set_avatar_type, set_avatar_name, confirm_avatar, edit_avatar_name

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

async def show_avatar_confirm(chat_id, user_id, avatar_id, session):
    """
    Показывает подтверждение создания аватара.
    
    Args:
        chat_id (int): ID чата
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
    """
    # Валидация аватара
    is_valid, msg = await validate_avatar_exists(user_id, avatar_id, session)
    if not is_valid:
        await bot.send_message(chat_id, f"Ошибка: {msg}")
        return
        
    # Валидация фото
    is_valid, msg = await validate_avatar_photos(user_id, avatar_id, session)
    if not is_valid:
        await bot.send_message(chat_id, f"Ошибка: {msg}")
        return
        
    # Получаем данные аватара
    from frontend_bot.services.avatar_manager import get_avatar_data
    avatar_data = await get_avatar_data(user_id, avatar_id, session)
    
    if not avatar_data:
        await bot.send_message(chat_id, "Ошибка: не удалось получить данные аватара")
        return
        
    # Формируем текст подтверждения
    text = AVATAR_CONFIRM_TEXT.format(
        title=avatar_data.get("title", "-"),
        gender=avatar_data.get("gender", "-"),
        photo_count=len(avatar_data.get("photos", [])),
        price=150,  # TODO: брать из конфига
        balance=250,  # TODO: брать из баланса пользователя
    )
    
    # Отправляем сообщение с подтверждением
    await bot.send_message(
        chat_id,
        text,
        parse_mode="HTML",
        reply_markup=avatar_confirm_keyboard(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_yes")
async def handle_avatar_confirm_yes(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(call.message.chat.id, "Ошибка: не найден аватар.")
        await bot.answer_callback_query(call.id)
        return
    async with AsyncSessionLocal() as session:
        await confirm_avatar(user_id, avatar_id, session)
    await bot.send_message(call.message.chat.id, "Аватар успешно создан! 🎉")
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_edit")
async def handle_avatar_confirm_edit(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(call.message.chat.id, "Ошибка: не найден аватар.")
        await bot.answer_callback_query(call.id)
        return
    async with AsyncSessionLocal() as session:
        await edit_avatar_name(user_id, avatar_id, session)
    await bot.send_message(call.message.chat.id, "Введите новое имя для аватара:")
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data in ["avatar_type_man", "avatar_type_woman"])
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
            await set_avatar_type(user_id, avatar_id, gender, session)
    else:
        await set_avatar_type(user_id, avatar_id, gender, session)
    await bot.send_message(call.message.chat.id, "Введите имя для вашего аватара:")
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text not in ["⬅️ Назад", "Отмена"])
async def handle_avatar_name_input(message, db: AsyncSession = None):
    user_id = message.from_user.id
    state = await get_state(user_id, db)
    if state != "avatar_enter_name":
        return
    name = message.text.strip()
    if not name:
        await bot.send_message(message.chat.id, PHOTO_NAME_EMPTY)
        return
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        await bot.send_message(message.chat.id, "Ошибка: не найден аватар.")
        return
    session = db
    if session is None:
        from frontend_bot.database import get_async_session
        async with get_async_session() as session:
            await set_avatar_name(user_id, avatar_id, name, session)
    else:
        await set_avatar_name(user_id, avatar_id, name, session)
    # ... остальной код (показ подтверждения и т.д.) ...

# Остальные обработчики (handle_avatar_confirm_edit,
# handle_avatar_cancel, handle_create_avatar) переносить по аналогии...
