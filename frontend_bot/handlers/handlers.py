"""
Обработчики сообщений бота.
"""

from functools import wraps
from frontend_bot.bot_instance import bot
from frontend_bot.services.state_utils import set_state, get_state
from frontend_bot.services.avatar_workflow import (
    handle_photo_upload,
    handle_gender_selection,
    handle_name_input,
    finalize_avatar,
    handle_creation_error,
    PhotoValidationError,
    ValidationError,
    cleanup_state,
)
from frontend_bot.services.avatar_manager import load_avatar_fsm
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import (
    avatar_photo_keyboard,
    avatar_gender_keyboard,
    avatar_name_keyboard,
    avatar_confirm_keyboard,
)
from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
import logging

logger = logging.getLogger(__name__)

def handle_avatar_state(func):
    """
    Декоратор для обработки общих случаев в хендлерах аватаров.
    
    Args:
        func: Функция-хендлер
        
    Returns:
        Обернутая функция
    """
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        try:
            user_id = message.from_user.id
            avatar_id = await get_state(user_id)
            
            if not avatar_id:
                await bot.send_message(
                    message.chat.id,
                    "Ошибка: не найден активный процесс создания аватара. Пожалуйста, начните заново.",
                    reply_markup=main_menu_keyboard()
                )
                await set_state(user_id, "main_menu")
                return
                
            return await func(message, user_id, avatar_id, *args, **kwargs)
            
        except (PhotoValidationError, ValidationError) as e:
            await handle_creation_error(user_id, message.chat.id, e)
            await cleanup_state(user_id)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            await bot.send_message(
                message.chat.id,
                "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard()
            )
            await set_state(user_id, "main_menu")
            
    return wrapper

async def check_photo_upload_state(message):
    """Проверяет состояние загрузки фото."""
    return await get_state(message.from_user.id) == "avatar_photo_upload"

async def check_photo_next_state(message):
    """Проверяет состояние перехода к следующему шагу."""
    return await get_state(message.from_user.id) == "avatar_photo_upload" and message.text == "Далее"

async def check_gender_state(message):
    """Проверяет состояние выбора пола."""
    return await get_state(message.from_user.id) == "avatar_gender"

async def check_name_state(message):
    """Проверяет состояние ввода имени."""
    return await get_state(message.from_user.id) == "avatar_enter_name"

async def check_confirm_state(message):
    """Проверяет состояние подтверждения."""
    return await get_state(message.from_user.id) == "avatar_confirm" and message.text == "Подтвердить"

@bot.message_handler(func=check_photo_upload_state, content_types=['photo'])
@handle_avatar_state
async def handle_avatar_photo(message, user_id, avatar_id):
    """Обработчик загрузки фото для аватара."""
    # Получаем фото максимального размера
    photo = max(message.photo, key=lambda x: x.file_size)
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    # Обрабатываем загрузку фото
    await handle_photo_upload(user_id, avatar_id, downloaded_file, photo.file_id)
    
    # Получаем текущее количество фото
    data = await load_avatar_fsm(user_id, avatar_id)
    photos_count = len(data.get("photos", []))
    
    # Отправляем сообщение о статусе
    await bot.send_message(
        message.chat.id,
        f"Фото успешно загружено! Загружено фото: {photos_count}/{AVATAR_MAX_PHOTOS}\n"
        f"Минимум требуется: {AVATAR_MIN_PHOTOS} фото.\n"
        "Продолжайте загружать фото или нажмите 'Далее' для перехода к следующему шагу.",
        reply_markup=avatar_photo_keyboard()
    )
    await set_state(user_id, "avatar_photo_upload")

@bot.message_handler(func=check_photo_next_state)
@handle_avatar_state
async def handle_avatar_photo_next(message, user_id, avatar_id):
    """Обработчик перехода к следующему шагу после загрузки фото."""
    # Проверяем количество фото
    data = await load_avatar_fsm(user_id, avatar_id)
    photos_count = len(data.get("photos", []))
    
    if photos_count < AVATAR_MIN_PHOTOS:
        await bot.send_message(
            message.chat.id,
            f"Недостаточно фото! Требуется минимум {AVATAR_MIN_PHOTOS} фото. "
            f"Текущее количество: {photos_count}",
            reply_markup=avatar_photo_keyboard()
        )
        return
        
    # Переходим к выбору пола
    await bot.send_message(
        message.chat.id,
        "Выберите пол для аватара:",
        reply_markup=avatar_gender_keyboard()
    )
    await set_state(user_id, "avatar_gender")

@bot.message_handler(func=check_gender_state)
@handle_avatar_state
async def handle_avatar_gender(message, user_id, avatar_id):
    """Обработчик выбора пола для аватара."""
    # Обрабатываем выбор пола
    gender = "male" if message.text == "Мужской" else "female"
    await handle_gender_selection(user_id, avatar_id, gender)
    
    # Запрашиваем имя
    await bot.send_message(
        message.chat.id,
        "Введите имя для аватара:",
        reply_markup=avatar_name_keyboard()
    )
    await set_state(user_id, "avatar_enter_name")

@bot.message_handler(func=check_name_state)
@handle_avatar_state
async def handle_avatar_name(message, user_id, avatar_id):
    """Обработчик ввода имени для аватара."""
    # Обрабатываем ввод имени
    await handle_name_input(user_id, avatar_id, message.text)
    
    # Запрашиваем подтверждение
    await bot.send_message(
        message.chat.id,
        "Проверьте данные аватара и подтвердите создание:",
        reply_markup=avatar_confirm_keyboard()
    )
    await set_state(user_id, "avatar_confirm")

@bot.message_handler(func=check_confirm_state)
@handle_avatar_state
async def handle_avatar_confirm(message, user_id, avatar_id):
    """Обработчик подтверждения создания аватара."""
    # Завершаем создание аватара
    await finalize_avatar(user_id, avatar_id)
    
    # Отправляем сообщение об успехе
    await bot.send_message(
        message.chat.id,
        "Аватар успешно создан!",
        reply_markup=main_menu_keyboard()
    )
    await set_state(user_id, "main_menu") 