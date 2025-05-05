from frontend_bot.config import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS, PROGRESSBAR_EMOJI_FILLED, PROGRESSBAR_EMOJI_CURRENT, PROGRESSBAR_EMOJI_EMPTY
from frontend_bot.services.state_manager import clear_state, set_current_avatar_id
from frontend_bot.bot import bot
import asyncio
from frontend_bot.handlers.avatar.state import user_session, user_gallery

# Прогресс-бар

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

# --- FSM/Session утилиты ---

def reset_avatar_fsm(user_id):
    user_session.pop(user_id, None)
    for key in list(user_gallery.keys()):
        if key[0] == user_id:
            user_gallery.pop(key, None)
    clear_state(user_id)
    set_current_avatar_id(user_id, None)

def start_avatar_wizard_for_user(user_id, chat_id):
    from uuid import uuid4
    from frontend_bot.texts.avatar.texts import PHOTO_REQUIREMENTS_TEXT
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
    from frontend_bot.services.avatar_manager import init_avatar_fsm
    from frontend_bot.services.state_manager import set_state
    init_avatar_fsm(user_id, avatar_id)
    set_state(user_id, "avatar_photo_upload")
    set_current_avatar_id(user_id, avatar_id)
    requirements = PHOTO_REQUIREMENTS_TEXT
    async def send_requirements():
        msg = await bot.send_message(chat_id, requirements, parse_mode="HTML")
        user_session[user_id]['wizard_message_ids'].append(msg.message_id)
    asyncio.create_task(send_requirements())

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
    from frontend_bot.services.avatar_manager import load_avatar_fsm
    data = load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    count = len(photos)
    msg_id = user_session[user_id].get('last_info_msg_id')
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    text = get_photo_hint_text(count, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS)
    msg = await bot.send_message(chat_id, text)
    user_session[user_id]['last_info_msg_id'] = msg.message_id

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

# Остальные утилиты (reset, start_wizard_for_user, get_photo_hint_text, update_photo_hint, delete_last_error_message, delete_last_info_message)
# ... переносить по аналогии ... 