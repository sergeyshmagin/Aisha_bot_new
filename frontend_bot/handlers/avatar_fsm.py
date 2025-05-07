import logging
import traceback
import asyncio

from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from frontend_bot.services.avatar_manager import (
    init_avatar_fsm,
    load_avatar_fsm,
    add_photo_to_avatar,
    remove_photo_from_avatar,
    update_avatar_fsm,
    validate_photo,
    save_avatar_fsm,
    clear_avatar_fsm,
    mark_avatar_ready
)
from frontend_bot.services.state_manager import (
    set_state,
    get_state,
    set_current_avatar_id,
    get_current_avatar_id,
    clear_state
)
from uuid import uuid4
import time

from frontend_bot.bot import bot  # Импортируем и используем глобальный bot

# Импорт main_menu_keyboard, если нет — временная заглушка
try:
    from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
except ImportError:
    def main_menu_keyboard():
        return None

from frontend_bot.keyboards.reply import my_avatars_keyboard
from frontend_bot.texts.avatar.texts import (
    PHOTO_REQUIREMENTS_TEXT
)

from frontend_bot.config import (
    AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS,
    PROGRESSBAR_EMOJI_FILLED, PROGRESSBAR_EMOJI_CURRENT, PROGRESSBAR_EMOJI_EMPTY,
    FAL_MODE, FAL_ITERATIONS, FAL_PRIORITY, FAL_CAPTIONING, FAL_TRIGGER_WORD, FAL_LORA_RANK, FAL_FINETUNE_TYPE,
    FAL_WEBHOOK_URL
)

from frontend_bot.services.fal_trainer import train_avatar

# Словари для отображения типа и модели
AVATAR_TYPE_DISPLAY = {
    'man': 'Мужчина',
    'woman': 'Женщина',
    'boy': 'Мальчик',
    'girl': 'Девочка',
    'cat': 'Кот',
    'dog': 'Собака',
}
AVATAR_MODEL_DISPLAY = {
    'Flux1.dev': 'Фотореалистичная',
}

# Клавиатура отмены
cancel_keyboard = InlineKeyboardMarkup()
cancel_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# Клавиатура выбора типа
type_keyboard = InlineKeyboardMarkup()
type_keyboard.add(
    InlineKeyboardButton(
        "👨 Мужчина", callback_data="avatar_type_man"
    ),
    InlineKeyboardButton(
        "👩 Женщина", callback_data="avatar_type_woman"
    )
)

# Клавиатура выбора базовой модели
base_model_keyboard = InlineKeyboardMarkup()
base_model_keyboard.add(
    InlineKeyboardButton(
        "Flux1.dev (рекомендуется)", callback_data="avatar_base_flux1"
    )
)
# Можно добавить другие модели при необходимости

# Клавиатура выбора стиля
style_keyboard = InlineKeyboardMarkup()
style_keyboard.add(
    InlineKeyboardButton("Реалистичный", callback_data="avatar_style_realistic"),
    InlineKeyboardButton("Мультяшный", callback_data="avatar_style_cartoon"),
    InlineKeyboardButton("Аниме", callback_data="avatar_style_anime"),
    InlineKeyboardButton("3D", callback_data="avatar_style_3d")
)
style_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# Клавиатура после 16 фото
continue_keyboard = InlineKeyboardMarkup()
continue_keyboard.add(
    InlineKeyboardButton("Продолжить", callback_data="avatar_next")
)
continue_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# Клавиатура только для продолжения
only_continue_keyboard = InlineKeyboardMarkup()
only_continue_keyboard.add(
    InlineKeyboardButton("Продолжить", callback_data="avatar_next")
)
only_continue_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# Inline-клавиатура для этапа загрузки фото
photo_stage_keyboard = InlineKeyboardMarkup()
photo_stage_keyboard.add(
    InlineKeyboardButton("📷 Мои фото", callback_data="avatar_show_photos"),
    InlineKeyboardButton("ℹ️ Требования", callback_data="avatar_show_requirements"),
    InlineKeyboardButton("👀 Пример фото", callback_data="avatar_show_example")
)
photo_stage_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# --- Объединённые структуры ---
user_session = {}  # user_id -> dict: wizard_message_ids, last_wizard_state,
                   # uploaded_photo_msgs, last_error_msg, last_info_msg_id
user_gallery = {}  # (user_id, avatar_id) -> dict: index, last_switch

# Очередь media_group для каждого пользователя
user_media_group_queue = {}  # user_id -> list of (media_group_id, photos)
user_media_group_processing = set()  # user_id, если сейчас идёт обработка

# --- Буферы для фото ---
user_single_photo_buffer = {}  # user_id -> [photo_bytes, ...]
user_media_group_buffer = {}   # user_id -> media_group_id -> [photo_bytes, ...]
user_media_group_timers = {}   # user_id -> media_group_id -> asyncio.Task
user_single_photo_timer = {}   # user_id -> asyncio.Task

# Инициализация логгера
logger = logging.getLogger(__name__)

user_locks = {}

async def send_and_track(user_id, chat_id, *args, **kwargs):
    msg = await bot.send_message(chat_id, *args, **kwargs)
    user_session[user_id]['wizard_message_ids'].append(msg.message_id)
    return msg

async def start_avatar_wizard(message: Message):
    logger.info(
        f"[AVATAR FSM] Запуск визарда для user_id={message.from_user.id}"
    )
    user_id = message.from_user.id
    avatar_id = str(uuid4())
    # Инициализация user_session и user_gallery
    user_session[user_id] = {
        'wizard_message_ids': [],
        'last_wizard_state': None,
        'uploaded_photo_msgs': [],
        'last_error_msg': None,
        'last_info_msg_id': None
    }
    user_gallery[(user_id, avatar_id)] = {
        'index': 0,
        'last_switch': 0
    }
    # Передаём class_name если есть (по умолчанию пусто)
    init_avatar_fsm(user_id, avatar_id, class_name="")
    set_state(user_id, "avatar_photo_upload")
    set_current_avatar_id(user_id, avatar_id)
    requirements = PHOTO_REQUIREMENTS_TEXT
    await send_and_track(
        user_id,
        message.chat.id,
        requirements,
        parse_mode="HTML"
    )
    logger.info(
        f"[DEBUG] После запуска визарда: user_id={user_id}, "
        f"state={get_state(user_id)}, "
        f"avatar_id={get_current_avatar_id(user_id)}"
    )

def get_progressbar(
    current,
    total,
    min_photos=AVATAR_MIN_PHOTOS,
    max_photos=AVATAR_MAX_PHOTOS,
    current_idx=None
):
    if current <= min_photos:
        bar_len = min_photos
    else:
        bar_len = max_photos
    bar = []
    for i in range(bar_len):
        if current_idx is not None and i == current_idx:
            bar.append(PROGRESSBAR_EMOJI_CURRENT)  # текущее фото
        elif i < current:
            bar.append(PROGRESSBAR_EMOJI_FILLED)  # заполнено
        else:
            bar.append(PROGRESSBAR_EMOJI_EMPTY)  # пусто
    return f"{''.join(bar)} ({current}/{bar_len})"

user_media_groups = {}  # (user_id, media_group_id) -> [(file_id, photo_bytes), ...]

@bot.message_handler(content_types=['photo'])
async def handle_avatar_photo_upload(message: Message):
    user_id = message.from_user.id
    logger.info(f"[FSM] handle_avatar_photo_upload: user_id={user_id}, message_id={message.message_id}")
    state = get_state(user_id)
    avatar_id = get_current_avatar_id(user_id)
    logger.info(f"[FSM] handle_avatar_photo_upload: state={state}, avatar_id={avatar_id}")
    if state != "avatar_photo_upload" or not avatar_id:
        logger.info(f"[FSM] handle_avatar_photo_upload: state not valid or no avatar_id")
        return
    file_info = await bot.get_file(message.photo[-1].file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    media_group_id = getattr(message, 'media_group_id', None)
    logger.info(f"[FSM] handle_avatar_photo_upload: media_group_id={media_group_id}")
    # --- Если это media_group ---
    if media_group_id:
        if user_id not in user_media_group_buffer:
            user_media_group_buffer[user_id] = {}
        if media_group_id not in user_media_group_buffer[user_id]:
            user_media_group_buffer[user_id][media_group_id] = []
        user_media_group_buffer[user_id][media_group_id].append((message.photo[-1].file_id, downloaded_file, message.message_id))
        # Сбросить старый таймер, если был
        if user_id in user_media_group_timers and media_group_id in user_media_group_timers[user_id]:
            user_media_group_timers[user_id][media_group_id].cancel()
        # Запустить новый таймер
        task = asyncio.create_task(flush_media_group(user_id, media_group_id, message.chat.id, avatar_id))
        if user_id not in user_media_group_timers:
            user_media_group_timers[user_id] = {}
        user_media_group_timers[user_id][media_group_id] = task
        return
    # --- Если это одиночное фото (или forward пачкой) ---
    if user_id not in user_single_photo_buffer:
        user_single_photo_buffer[user_id] = []
    user_single_photo_buffer[user_id].append((message.photo[-1].file_id, downloaded_file, message.message_id))
    # Запустить таймер только если его нет или он завершён
    if user_id not in user_single_photo_timer or user_single_photo_timer[user_id].done():
        task = asyncio.create_task(flush_single_photo_buffer(user_id, message.chat.id, avatar_id))
        user_single_photo_timer[user_id] = task
    return

async def flush_single_photo_buffer(user_id, chat_id, avatar_id):
    logger.info(f"[FSM] flush_single_photo_buffer called for user_id={user_id}, avatar_id={avatar_id}")
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            photos = user_single_photo_buffer.pop(user_id, [])
            logger.info(f"[FSM] flush_single_photo_buffer: {len(photos)} photos to process")
            for file_id, photo_bytes, msg_id in photos:
                logger.info(f"[FSM] flush_single_photo_buffer: Processing photo {file_id}")
                data = load_avatar_fsm(user_id, avatar_id)
                logger.info(f"[FSM] flush_single_photo_buffer: loaded data.json: {data}")
                existing_photos = data.get("photos", [])
                existing_paths = [p["path"] if isinstance(p, dict) else p for p in existing_photos]
                is_valid, result = validate_photo(photo_bytes, existing_paths)
                logger.info(f"[FSM] flush_single_photo_buffer: validate_photo: {is_valid}, {result}")
                if not is_valid:
                    await delete_last_error_message(user_id, chat_id)
                    # Всегда удаляем исходное фото
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except Exception:
                        pass
                    from io import BytesIO
                    text = None
                    if "Такое фото уже загружено" in result:
                        text = (
                            "⚠️ Фото не принято: Такое фото уже загружено.\n"
                            "📸 Совет: используйте чёткие фото без фильтров."
                        )
                    else:
                        text = f"⚠️ Фото не принято: {result}\n📸 Совет: используйте чёткие фото без фильтров."
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
                    await bot.send_photo(
                        chat_id,
                        BytesIO(photo_bytes),
                        caption=text,
                        reply_markup=markup
                    )
                    user_session[user_id]['last_error_msg'] = None
                    continue
                await delete_last_error_message(user_id, chat_id)
                logger.info(f"[FSM] flush_single_photo_buffer: calling add_photo_to_avatar")
                photo_path = add_photo_to_avatar(user_id, avatar_id, photo_bytes, file_id=file_id)
                logger.info(f"[FSM] flush_single_photo_buffer: Photo added at {photo_path}")
                data = load_avatar_fsm(user_id, avatar_id)
                logger.info(f"[FSM] flush_single_photo_buffer: data after add_photo: {data}")
                # update_photo_hint больше не вызываем здесь, так как галерея покажет прогресс
                data["photos"][-1] = {"path": photo_path, "file_id": file_id}
                save_avatar_fsm(user_id, avatar_id, data)
                logger.info(f"[FSM] flush_single_photo_buffer: data after save_avatar_fsm: {data}")
                # Удаляем исходное сообщение с фото
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            # После всей пачки — только обновить прогресс, не показывать галерею
            data = load_avatar_fsm(user_id, avatar_id)
            photos = data.get("photos", [])
            msg_id = user_session[user_id]['wizard_message_ids'][-1] if user_session[user_id]['wizard_message_ids'] else None
            await notify_progress(chat_id, user_id, avatar_id, len(photos), msg_id)
            # Если достигнут лимит — показать галерею и перевести в review
            if len(photos) >= AVATAR_MAX_PHOTOS:
                set_state(user_id, "avatar_gallery_review")
                await show_wizard_gallery(chat_id, user_id, avatar_id, photos, len(photos)-1 if photos else 0)
    except Exception as e:
        logger.error(f"Ошибка: {e}\n{traceback.format_exc()}")

async def flush_media_group(user_id, media_group_id, chat_id, avatar_id):
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    async with user_locks[user_id]:
        logger.debug(f"[LOCK] user_id={user_id} lock acquired (media group)")
        await asyncio.sleep(1.5)
        photos = user_media_group_buffer[user_id].pop(media_group_id, [])
        for file_id, photo_bytes, msg_id in photos:
            data = load_avatar_fsm(user_id, avatar_id)
            existing_photos = data.get("photos", [])
            existing_paths = [p["path"] if isinstance(p, dict) else p for p in existing_photos]
            is_valid, result = validate_photo(photo_bytes, existing_paths)
            if not is_valid:
                await delete_last_error_message(user_id, chat_id)
                # Всегда удаляем исходное фото
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
                from io import BytesIO
                text = None
                if "Такое фото уже загружено" in result:
                    text = (
                        "⚠️ Фото не принято: Такое фото уже загружено.\n"
                        "📸 Совет: используйте чёткие фото без фильтров."
                    )
                else:
                    text = f"⚠️ Фото не принято: {result}\n📸 Совет: используйте чёткие фото без фильтров."
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
                await bot.send_photo(
                    chat_id,
                    BytesIO(photo_bytes),
                    caption=text,
                    reply_markup=markup
                )
                user_session[user_id]['last_error_msg'] = None
                continue
            await delete_last_error_message(user_id, chat_id)
            photo_path = add_photo_to_avatar(user_id, avatar_id, photo_bytes, file_id=file_id)
            data = load_avatar_fsm(user_id, avatar_id)
            data["photos"][-1] = {"path": photo_path, "file_id": file_id}
            save_avatar_fsm(user_id, avatar_id, data)
            # update_photo_hint больше не вызываем здесь, так как галерея покажет прогресс
            # Удаляем исходное сообщение с фото
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
        # После всей пачки — только обновить прогресс, не показывать галерею
        data = load_avatar_fsm(user_id, avatar_id)
        photos = data.get("photos", [])
        msg_id = user_session[user_id]['wizard_message_ids'][-1] if user_session[user_id]['wizard_message_ids'] else None
        await notify_progress(chat_id, user_id, avatar_id, len(photos), msg_id)
        # Если достигнут лимит — показать галерею и перевести в review
        if len(photos) >= AVATAR_MAX_PHOTOS:
            set_state(user_id, "avatar_gallery_review")
            await show_wizard_gallery(chat_id, user_id, avatar_id, photos, len(photos)-1 if photos else 0)
    logger.debug(f"[LOCK] user_id={user_id} lock released (media group)")

@bot.callback_query_handler(func=lambda call: call.data == "avatar_next")
async def handle_avatar_next(call):
    user_id = call.from_user.id
    await bot.send_message(
        call.message.chat.id,
        "Выберите стиль для вашего аватара:",
        reply_markup=style_keyboard
    )
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "avatar_title")
async def handle_avatar_title(message: Message):
    user_id = message.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    # Удаляем предыдущее активное сообщение
    for mid in user_session[user_id]['wizard_message_ids']:
        try:
            await bot.delete_message(message.chat.id, mid)
        except Exception:
            pass
    user_session[user_id]['wizard_message_ids'] = []
    if not avatar_id:
        await bot.send_message(
            message.chat.id,
            "Ошибка: не найден идентификатор аватара. Пожалуйста, начните создание аватара заново.",
            reply_markup=main_menu_keyboard() if 'main_menu_keyboard' in globals() else None
        )
        reset_avatar_fsm(user_id)
        return
    title = message.text.strip()
    if not title:
        msg = await bot.send_message(
            message.chat.id,
            "Имя не может быть пустым. Введите имя для аватара:",
            reply_markup=cancel_keyboard
        )
        user_session[user_id]['wizard_message_ids'] = [msg.message_id]
        return
    # Сохраняем имя в FSM
    update_avatar_fsm(user_id, avatar_id, title=title)
    set_state(user_id, "avatar_confirm")
    data = load_avatar_fsm(user_id, avatar_id)
    class_name = data.get('class_name', '')
    display_type = AVATAR_TYPE_DISPLAY.get(class_name, class_name)
    photos = data.get('photos', [])
    # Здесь можно получить стоимость и баланс (заглушки)
    avatar_price = 150  # TODO: заменить на реальную логику
    user_balance = 250  # TODO: заменить на реальную логику
    # Формируем текст подтверждения
    confirm_text = (
        "🦋 <b>Проверьте данные аватара</b>\n\n"
        f"🏷 Имя: {title}\n"
        f"{'👨‍🦰' if class_name == 'man' else '👩‍🦰'} Пол: {display_type}\n"
        f"🖼 Фото: {len(photos)}\n"
        f"💎 Стоимость: {avatar_price}\n"
        f"💰 Ваш баланс: {user_balance}\n\n"
        "Если всё верно, нажмите <b>Создать аватар</b>.\n"
        "Для изменений — выберите 'Изменить'."
    )
    # Inline-клавиатура подтверждения
    confirm_keyboard = InlineKeyboardMarkup()
    confirm_keyboard.add(
        InlineKeyboardButton("✅ Создать аватар", callback_data="avatar_confirm_yes"),
        InlineKeyboardButton("✏️ Изменить", callback_data="avatar_confirm_edit")
    )
    confirm_keyboard.add(
        InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
    )
    msg = await bot.send_message(
        message.chat.id,
        confirm_text,
        reply_markup=confirm_keyboard,
        parse_mode="HTML"
    )
    user_session[user_id]['wizard_message_ids'] = [msg.message_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_type_"))
async def handle_avatar_type(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    # Удаляем предыдущее активное сообщение
    for mid in user_session[user_id]['wizard_message_ids']:
        try:
            await bot.delete_message(call.message.chat.id, mid)
        except Exception:
            pass
    user_session[user_id]['wizard_message_ids'] = []
    # Удаляем сообщение с меню выбора типа
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    type_name = call.data.split("_")[-1]
    update_avatar_fsm(user_id, avatar_id, class_name=type_name, base_tune="Flux1.dev")
    set_state(user_id, "avatar_title")
    msg = await bot.send_message(
        call.message.chat.id,
        "Теперь введите имя для вашего аватара:",
        reply_markup=cancel_keyboard
    )
    user_session[user_id]['wizard_message_ids'] = [msg.message_id]
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_style_"))
async def handle_avatar_style(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    style = call.data.split("_")[-1]
    update_avatar_fsm(user_id, avatar_id, style=style)
    set_state(user_id, "avatar_confirm")
    # Итоговый предпросмотр и подтверждение
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    title = data.get("title", "")
    class_name = data.get("class_name", "")
    base_tune = data.get("base_tune", "")
    style_name = style
    # Прогрессбар и предпросмотр фото
    preview_text = (
        f"\U0001F4F7 Фото: {len(photos)}\n"
        f"Имя: {title}\n"
        f"Тип: {class_name}\n"
        f"Базовая модель: {base_tune}\n"
        f"Стиль: {style_name}\n\n"
        "Проверьте данные. Всё верно?"
    )
    confirm_keyboard = InlineKeyboardMarkup()
    confirm_keyboard.add(
        InlineKeyboardButton("Подтвердить", callback_data="avatar_confirm_yes"),
        InlineKeyboardButton("Изменить", callback_data="avatar_confirm_edit")
    )
    await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, 0, message_id=call.message.message_id)
    await bot.send_message(
        call.message.chat.id,
        preview_text,
        reply_markup=confirm_keyboard
    )
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_confirm_edit")
async def handle_avatar_confirm_edit(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    set_state(user_id, "avatar_gallery_review")
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    logger.info(f"[AVATAR FSM] avatar_confirm_edit: user_id={user_id}, avatar_id={avatar_id}, photos={len(photos)}")
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    if not photos:
        await bot.send_message(
            call.message.chat.id,
            "Нет фото для отображения. Пожалуйста, загрузите хотя бы одно фото."
        )
        return
    # Сброс last_wizard_state для принудительного показа галереи
    user_session[user_id]['last_wizard_state'] = None
    try:
        await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, 0)
    except Exception as e:
        logger.error(f"Ошибка показа галереи: {e}")
        await bot.send_message(
            call.message.chat.id,
            "Ошибка при отображении галереи. Попробуйте ещё раз или обратитесь в поддержку."
        )
    await bot.answer_callback_query(call.id)

# Обработчик предпросмотра всех фото
@bot.callback_query_handler(func=lambda call: call.data == "avatar_show_photos")
async def handle_show_photos(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    if not photos:
        await bot.send_message(call.message.chat.id, "У вас пока нет загруженных фото.")
    else:
        # Запускаем галерею с первого фото
        await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, 0)
    await bot.answer_callback_query(call.id)

user_gallery_index = {}  # (user_id, avatar_id) -> int
user_gallery_last_switch = {}  # (user_id, avatar_id) -> timestamp

def get_full_gallery_keyboard(idx, total):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data="avatar_gallery_prev"),
        InlineKeyboardButton("❌ Удалить", callback_data="avatar_gallery_delete"),
        InlineKeyboardButton("Вперёд ▶️", callback_data="avatar_gallery_next")
    )
    if total >= AVATAR_MIN_PHOTOS:
        markup.row(InlineKeyboardButton("✅ Продолжить", callback_data="avatar_gallery_continue"))
    markup.row(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup

async def show_wizard_gallery(chat_id, user_id, avatar_id, photos, idx, message_id=None):
    logger.info(f"[show_wizard_gallery] user_id={user_id}, avatar_id={avatar_id}, idx={idx}, message_id={message_id}, photos={len(photos)}")
    instruction = PHOTO_REQUIREMENTS_TEXT
    if not photos:
        new_text = instruction
        new_markup = get_full_gallery_keyboard(0, 0)
        last = user_session[user_id]['last_wizard_state']
        logger.info(f"[show_wizard_gallery] last_wizard_state={last}")
        if last and last[0] == new_text and last[1].to_dict() == new_markup.to_dict():
            logger.info("[show_wizard_gallery] return: no change (no photos)")
            return  # Не изменилось — не редактируем
        if message_id:
            await bot.edit_message_text(
                new_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=new_markup
            )
            await clear_old_wizard_messages(chat_id, user_id, message_id)
            user_session[user_id]['last_wizard_state'] = (new_text, new_markup)
        else:
            msg = await bot.send_message(chat_id, new_text, reply_markup=new_markup)
            await clear_old_wizard_messages(chat_id, user_id, msg.message_id)
            user_session[user_id]['last_wizard_state'] = (new_text, new_markup)
        logger.info("[show_wizard_gallery] return: sent requirements (no photos)")
        return
    idx = max(0, min(idx, len(photos) - 1))
    user_gallery[(user_id, avatar_id)]['index'] = idx
    photo = photos[idx]
    if isinstance(photo, dict):
        file_id = photo.get("file_id")
        photo_path = photo.get("path")
    else:
        file_id = None
        photo_path = photo
    total = len(photos)
    progress = get_progressbar(
        total, AVATAR_MAX_PHOTOS, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS, idx
    )
    left = AVATAR_MAX_PHOTOS - total
    if total == AVATAR_MIN_PHOTOS:
        caption = (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"✅ Вы загрузили минимально необходимое количество фото (<b>{AVATAR_MIN_PHOTOS}</b>).\n\n"
            f"🔝 Для лучшего качества генерации рекомендуем добавить ещё до <b>{AVATAR_MAX_PHOTOS}</b> фото.\n\n"
            f"➡️ Вы можете продолжить или добавить ещё фото."
        )
    elif AVATAR_MIN_PHOTOS < total < AVATAR_MAX_PHOTOS:
        caption = (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"🔝 Можно добавить ещё <b>{AVATAR_MAX_PHOTOS - total}</b> фото для лучшего качества.\n\n"
            f"➡️ Или продолжить к генерации аватара."
        )
    elif total == AVATAR_MAX_PHOTOS:
        caption = (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"Достигнут максимум фото. Можете только продолжить."
        )
    else:
        caption = (
            f"Фото {idx+1} из {total}\n{progress}\n\n"
            f"❗️Минимум для старта: <b>{AVATAR_MIN_PHOTOS}</b> фото.\n"
            f"Осталось загрузить: <b>{AVATAR_MIN_PHOTOS - total}</b> фото.\n\n"
            f"Добавьте ещё фото для лучшего качества."
        )
    keyboard = get_full_gallery_keyboard(idx, total)
    last = user_session[user_id]['last_wizard_state']
    logger.info(f"[show_wizard_gallery] last_wizard_state={last}")
    if last and last[0] == caption and last[1].to_dict() == keyboard.to_dict():
        logger.info("[show_wizard_gallery] return: no change (gallery)")
        return  # Не изменилось — не редактируем
    if message_id:
        try:
            if file_id:
                await bot.edit_message_media(
                    media=InputMediaPhoto(file_id, caption=caption, parse_mode="HTML"),
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard
                )
            else:
                with open(photo_path, 'rb') as img:
                    await bot.edit_message_media(
                        media=InputMediaPhoto(img, caption=caption, parse_mode="HTML"),
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=keyboard
                    )
            await clear_old_wizard_messages(chat_id, user_id, message_id)
            user_session[user_id]['last_wizard_state'] = (caption, keyboard)
            logger.info("[show_wizard_gallery] return: edit_message_media")
        except Exception as e:
            logger.error(f"[show_wizard_gallery] Exception: {e}")
            if file_id:
                msg = await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
            else:
                with open(photo_path, 'rb') as img:
                    msg = await bot.send_photo(chat_id, img, caption=caption, reply_markup=keyboard, parse_mode="HTML")
            await clear_old_wizard_messages(chat_id, user_id, msg.message_id)
            user_session[user_id]['wizard_message_ids'] = [msg.message_id]
            user_session[user_id]['last_wizard_state'] = (caption, keyboard)
            logger.info("[show_wizard_gallery] return: send_photo after exception")
    else:
        if file_id:
            msg = await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            with open(photo_path, 'rb') as img:
                msg = await bot.send_photo(chat_id, img, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        await clear_old_wizard_messages(chat_id, user_id, msg.message_id)
        user_session[user_id]['wizard_message_ids'] = [msg.message_id]
        user_session[user_id]['last_wizard_state'] = (caption, keyboard)
        logger.info("[show_wizard_gallery] return: send_photo (new message)")

@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_add")
async def handle_gallery_add(call):
    user_id = call.from_user.id
    # Не отправляем отдельное сообщение, просто уведомляем пользователя
    await bot.answer_callback_query(call.id, "Ждём новое фото...")

@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_continue")
async def handle_gallery_continue(call):
    user_id = call.from_user.id
    await show_type_menu(call.message.chat.id, user_id)
    await bot.answer_callback_query(call.id)

async def clear_old_wizard_messages(chat_id, user_id, keep_msg_id=None):
    """Удаляет все сообщения визарда, кроме указанного (актуального)."""
    msg_ids = user_session[user_id]['wizard_message_ids']
    for mid in msg_ids:
        if keep_msg_id is not None and mid == keep_msg_id:
            continue
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass
    # Оставляем только актуальный message_id
    if keep_msg_id:
        user_session[user_id]['wizard_message_ids'] = [keep_msg_id]
    else:
        user_session[user_id]['wizard_message_ids'] = []

@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_prev")
async def handle_gallery_prev(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    idx = user_gallery[(user_id, avatar_id)]['index']
    if not photos:
        await bot.answer_callback_query(call.id)
        return
    # Debounce: ограничиваем частоту переключения
    now = time.monotonic()
    last = user_gallery[(user_id, avatar_id)]['last_switch']
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[(user_id, avatar_id)]['last_switch'] = now
    if idx <= 0:
        idx = len(photos) - 1  # Циклически на последнее фото
    else:
        idx -= 1
    await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, idx, message_id=call.message.message_id)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_next")
async def handle_gallery_next(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    idx = user_gallery[(user_id, avatar_id)]['index']
    if not photos:
        await bot.answer_callback_query(call.id)
        return
    # Debounce: ограничиваем частоту переключения
    now = time.monotonic()
    last = user_gallery[(user_id, avatar_id)]['last_switch']
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[(user_id, avatar_id)]['last_switch'] = now
    if idx >= len(photos) - 1:
        idx = 0  # Циклически на первое фото
    else:
        idx += 1
    await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, idx, message_id=call.message.message_id)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_delete")
async def handle_gallery_delete(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    idx = user_gallery[(user_id, avatar_id)]['index']
    if not photos:
        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        await clear_old_wizard_messages(call.message.chat.id, user_id)
        reset_avatar_fsm(user_id)
        import asyncio
        await asyncio.sleep(0.5)
        start_avatar_wizard_for_user(user_id, call.message.chat.id)
        return
    await remove_photo_from_avatar(user_id, avatar_id, idx)
    data = load_avatar_fsm(user_id, avatar_id)  # обновляем после удаления
    photos = data.get("photos", [])
    # update_photo_hint вызываем только если фото не осталось
    if not photos:
        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        await clear_old_wizard_messages(call.message.chat.id, user_id)
        reset_avatar_fsm(user_id)
        import asyncio
        await asyncio.sleep(0.5)
        start_avatar_wizard_for_user(user_id, call.message.chat.id)
        return
    # После удаления сразу обновляем галерею
    new_idx = min(idx, len(photos) - 1)
    user_gallery[(user_id, avatar_id)]['index'] = new_idx
    await show_wizard_gallery(
        call.message.chat.id, user_id, avatar_id, photos, new_idx, message_id=call.message.message_id
    )
    await bot.answer_callback_query(call.id)

# Обработчик показа требований
@bot.callback_query_handler(func=lambda call: call.data == "avatar_show_requirements")
async def handle_show_requirements(call):
    requirements = PHOTO_REQUIREMENTS_TEXT
    await bot.send_message(call.message.chat.id, requirements, parse_mode="HTML")
    await bot.answer_callback_query(call.id)

# Обработчик показа примера фото
@bot.callback_query_handler(func=lambda call: call.data == "avatar_show_example")
async def handle_show_example(call):
    try:
        with open("frontend_bot/templates/example_good_photo.jpg", 'rb') as img:
            await bot.send_photo(call.message.chat.id, img, caption="👀 Пример хорошего фото: светлый фон, нейтральное выражение лица, хорошее освещение.")
    except Exception:
        await bot.send_message(call.message.chat.id, "Пример фото недоступен.")
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "📷 Создать аватар")
async def handle_create_avatar(message: Message):
    user_id = message.from_user.id
    state = get_state(user_id)
    # Если пользователь уже в процессе загрузки фото — не сбрасываем визард
    if state == "avatar_photo_upload" and get_current_avatar_id(user_id):
        await bot.send_message(
            message.chat.id,
            "Вы уже находитесь в процессе создания аватара. "
            "Можете продолжить загрузку фото или отменить процесс."
        )
        return
    # В любом другом состоянии — сбрасываем визард и запускаем новый
    reset_avatar_fsm(user_id)
    await start_avatar_wizard(message)

@bot.callback_query_handler(func=lambda call: call.data == "avatar_cancel")
async def handle_avatar_cancel(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    # Удаляем все wizard-сообщения пользователя
    if user_id in user_session:
        chat_id = call.message.chat.id
        for mid in user_session[user_id].get('wizard_message_ids', []):
            try:
                await bot.delete_message(chat_id, mid)
            except Exception:
                pass
        user_session[user_id]['wizard_message_ids'] = []
    # Удаляем все файлы и данные аватара, если есть avatar_id
    if avatar_id:
        clear_avatar_fsm(user_id, avatar_id)
    reset_avatar_fsm(user_id)  # Полный сброс FSM, фото и сессии
    await bot.send_message(
        call.message.chat.id,
        "Создание аватара отменено. Вы вернулись к списку аватаров.",
        reply_markup=my_avatars_keyboard()
    )
    await bot.answer_callback_query(call.id)

async def delete_last_error_message(user_id, chat_id):
    old_err = user_session[user_id]['last_error_msg']
    if old_err:
        try:
            await bot.delete_message(chat_id, old_err)
        except Exception:
            pass
        user_session[user_id]['last_error_msg'] = None

async def delete_last_info_message(user_id, chat_id):
    msg_id = user_session[user_id].get('last_info_msg_id')
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        user_session[user_id]['last_info_msg_id'] = None

async def notify_progress(chat_id, user_id, avatar_id, count, msg_id):
    # Индекс текущего фото для прогресс-бара — всегда 0 (или можно не выделять)
    progressbar = get_progressbar(
        count, AVATAR_MAX_PHOTOS, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS, 0
    )
    data = load_avatar_fsm(user_id, avatar_id)
    await delete_last_info_message(user_id, chat_id)
    if count < AVATAR_MAX_PHOTOS:
        await show_wizard_gallery(
            chat_id, user_id, avatar_id, data.get("photos", []), 0, message_id=msg_id
        )
    elif count == AVATAR_MAX_PHOTOS:
        await show_wizard_gallery(
            chat_id, user_id, avatar_id, data.get("photos", []), 0, message_id=msg_id
        )
    # Добавляем небольшую задержку для UX
    await asyncio.sleep(0.2)
    for mid in user_session[user_id]['uploaded_photo_msgs']:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass
    user_session[user_id]['uploaded_photo_msgs'] = []

# --- Новый сброс FSM ---
def reset_avatar_fsm(user_id):
    user_session.pop(user_id, None)
    # Удаляем все avatar_id пользователя из user_gallery
    for key in list(user_gallery.keys()):
        if key[0] == user_id:
            user_gallery.pop(key, None)
    clear_state(user_id)
    set_current_avatar_id(user_id, None)

# --- Новый запуск визарда без искусственного Message ---
def start_avatar_wizard_for_user(user_id, chat_id):
    avatar_id = str(uuid4())
    user_session[user_id] = {
        'wizard_message_ids': [],
        'last_wizard_state': None,
        'uploaded_photo_msgs': [],
        'last_error_msg': None,
        'last_info_msg_id': None
    }
    user_gallery[(user_id, avatar_id)] = {
        'index': 0,
        'last_switch': 0
    }
    init_avatar_fsm(user_id, avatar_id)
    set_state(user_id, "avatar_photo_upload")
    set_current_avatar_id(user_id, avatar_id)
    requirements = PHOTO_REQUIREMENTS_TEXT
    import asyncio
    async def send_requirements():
        msg = await bot.send_message(chat_id, requirements, parse_mode="HTML")
        user_session[user_id]['wizard_message_ids'].append(msg.message_id)
    asyncio.create_task(send_requirements())

async def process_user_media_group_queue(user_id, chat_id, avatar_id):
    user_media_group_processing.add(user_id)
    try:
        while user_media_group_queue.get(user_id):
            group = user_media_group_queue[user_id].pop(0)
            media_group_id, photos, wait_msg_id, n = group
            try:
                await asyncio.sleep(1.5)
                # Проверяем состояние перед обработкой
                if get_state(user_id) != "avatar_photo_upload":
                    continue  # Если этап уже сменился, не обновляем галерею и не отправляем сообщения
                data = load_avatar_fsm(user_id, avatar_id)
                count = len(data.get("photos", []))
                photos_left = AVATAR_MAX_PHOTOS - count
                if len(photos) > photos_left:
                    accepted_photos = photos[:photos_left]
                    skipped_photos = photos[photos_left:]
                else:
                    accepted_photos = photos
                    skipped_photos = []
                added = 0
                for file_id, photo_bytes in accepted_photos:
                    # Проверяем состояние перед каждым фото
                    if get_state(user_id) != "avatar_photo_upload":
                        continue
                    data = load_avatar_fsm(user_id, avatar_id)
                    existing_photos = data.get("photos", [])
                    existing_paths = [
                        p["path"] if isinstance(p, dict) else p
                        for p in existing_photos
                    ]
                    is_valid, result = validate_photo(photo_bytes, existing_paths)
                    if not is_valid:
                        await delete_last_error_message(user_id, chat_id)
                        # Всегда удаляем исходное фото
                        try:
                            await bot.delete_message(chat_id, wait_msg_id)
                        except Exception:
                            pass
                        from io import BytesIO
                        text = None
                        if "Такое фото уже загружено" in result:
                            text = (
                                "⚠️ Фото не принято: Такое фото уже загружено.\n"
                                "📸 Совет: используйте чёткие фото без фильтров."
                            )
                        else:
                            text = f"⚠️ Фото не принято: {result}\n📸 Совет: используйте чёткие фото без фильтров."
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
                        await bot.send_photo(
                            chat_id,
                            BytesIO(photo_bytes),
                            caption=text,
                            reply_markup=markup
                        )
                        user_session[user_id]['last_error_msg'] = None
                        continue
                    await delete_last_error_message(user_id, chat_id)
                    photo_path = add_photo_to_avatar(
                        user_id, avatar_id, photo_bytes, file_id=file_id
                    )
                    data = load_avatar_fsm(user_id, avatar_id)
                    data["photos"][-1] = {
                        "path": photo_path, "file_id": file_id
                    }
                    save_avatar_fsm(user_id, avatar_id, data)
                    added += 1
                # wait_msg_id больше не используется, удалять нечего
                data = load_avatar_fsm(user_id, avatar_id)
                msg_id = user_session[user_id]['wizard_message_ids'][-1] if user_session[user_id]['wizard_message_ids'] else None
                # Проверяем состояние перед обновлением галереи
                if get_state(user_id) == "avatar_photo_upload" and msg_id:
                    await show_wizard_gallery(
                        chat_id, user_id, avatar_id,
                        data.get("photos", []),
                        len(data.get("photos", [])) - 1,
                        message_id=msg_id
                    )
                await notify_progress(
                    chat_id, user_id, avatar_id, len(data.get("photos", [])), msg_id
                )
                # Добавляем небольшую задержку для UX
                await asyncio.sleep(0.2)
                for mid in user_session[user_id]['uploaded_photo_msgs']:
                    try:
                        await bot.delete_message(chat_id, mid)
                    except Exception:
                        pass
                user_session[user_id]['uploaded_photo_msgs'] = []
                total = len(data.get("photos", []))
                if skipped_photos:
                    await bot.send_message(
                        chat_id,
                        f"Можно загрузить не более {AVATAR_MAX_PHOTOS} фото. "
                        f"Приняты только первые {AVATAR_MAX_PHOTOS}."
                    )
                if total >= AVATAR_MAX_PHOTOS:
                    # Скрываем галерею (удаляем сообщение с фото)
                    for mid in user_session[user_id]['wizard_message_ids']:
                        try:
                            await bot.delete_message(chat_id, mid)
                        except Exception:
                            pass
                    user_session[user_id]['wizard_message_ids'] = []
                    # Переходим к выбору типа
                    set_state(user_id, "avatar_type")
                    await show_type_menu(chat_id, user_id)
                await notify_progress(
                    chat_id, user_id, avatar_id, total, msg_id
                )
            except Exception as e:
                logger.error(f"Ошибка альбома: {str(e)}\n{traceback.format_exc()}")
    finally:
        user_media_group_processing.discard(user_id)

# Вспомогательная функция для показа меню выбора типа
async def show_type_menu(chat_id, user_id):
    await clear_old_wizard_messages(chat_id, user_id)
    msg = await send_and_track(
        user_id,
        chat_id,
        "👤 Выберите пол для вашего аватара:\n\n"
        "Это важно для качества генерации. Пожалуйста, выберите тот вариант, который соответствует человеку на фото.",
        reply_markup=type_keyboard
    )
    return msg

def get_photo_hint_text(current, min_photos, max_photos):
    requirements = (
        f"Требования: фото должны быть разными, без фильтров, хорошее освещение. "
        f"Минимум: {min_photos}, максимум: {max_photos}."
    )
    if current < min_photos:
        return (
            f"✅ Принято: {current} фото из {min_photos}.\n"
            f"До минимума осталось: {min_photos - current} фото.\n\n"
            f"{requirements}"
        )
    elif current < max_photos:
        return (
            f"✅ Принято: {current} фото из {max_photos}.\n"
            f"Можно добавить ещё {max_photos - current} фото для лучшего результата.\n\n"
            f"{requirements}"
        )
    else:
        return (
            f"✅ Принято максимальное количество фото: {max_photos}.\n"
            f"{requirements}"
        )

async def update_photo_hint(user_id, chat_id, avatar_id):
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    count = len(photos)
    # Удаляем старую подсказку, если есть
    msg_id = user_session[user_id].get('last_info_msg_id')
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    text = get_photo_hint_text(count, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS)
    msg = await bot.send_message(chat_id, text)
    user_session[user_id]['last_info_msg_id'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data == "delete_error")
async def handle_delete_error(call):
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    await bot.answer_callback_query(call.id)
