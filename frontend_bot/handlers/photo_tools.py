from telebot.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import set_state, get_state
from frontend_bot.keyboards.reply import (
    photo_menu_keyboard, ai_photographer_keyboard,
    my_avatars_keyboard, build_avatars_keyboard
)
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.services.avatar_manager import get_avatars_index, clear_avatar_fsm, update_avatar_fsm
import os
from frontend_bot.handlers.avatar.state import user_session
import logging
import traceback

AVATARS_PER_PAGE = 3

def get_avatar_page(user_id):
    state = get_state(user_id)
    if state and state.startswith('avatars_page_'):
        try:
            return int(state.split('_')[-1])
        except Exception:
            return 0
    return 0

def set_avatar_page(user_id, page):
    set_state(user_id, f'avatars_page_{page}')


def build_pagination_keyboard(user_id, page, total):
    markup = InlineKeyboardMarkup()
    max_page = max(0, (total - 1) // AVATARS_PER_PAGE)
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton('◀️', callback_data='avatars_prev'))
    if page < max_page:
        buttons.append(InlineKeyboardButton('▶️', callback_data='avatars_next'))
    if buttons:
        markup.row(*buttons)
    return markup

@bot.message_handler(func=lambda m: m.text == "🖼 Мои аватары")
async def my_avatars_menu(message: Message, page: int = 0):
    set_state(message.from_user.id, f'avatars_page_{page}')
    user_id = message.from_user.id
    avatars = get_avatars_index(user_id)
    if not avatars:
        await bot.send_message(
            message.chat.id,
            "Пока у вас нет аватаров. Создайте первый! 🚀",
            reply_markup=my_avatars_keyboard()
        )
        return
    total = len(avatars)
    page = min(max(0, page), max(0, (total - 1) // AVATARS_PER_PAGE))
    start = page * AVATARS_PER_PAGE
    end = start + AVATARS_PER_PAGE
    for avatar in avatars[start:end]:
        preview_path = avatar.get('preview_path')
        gender = avatar.get('gender', 'unknown')
        gender_emoji = get_gender_emoji(gender)
        created_at = format_date(avatar.get('created_at'))
        status = format_status(avatar.get('status'))
        caption = (
            f"{gender_emoji} <b>{avatar.get('title', 'Без имени')}</b>\n"
            f"📅 {created_at}\n"
            f"⚡️ Статус: {status}"
        )
        markup = build_avatar_control_keyboard(avatar.get('avatar_id'))
        if preview_path and os.path.exists(preview_path):
            try:
                with open(preview_path, 'rb') as photo:
                    await bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=markup
                    )
            except Exception as e:
                await bot.send_message(
                    message.chat.id,
                    f"⚠️ Не удалось отправить превью: {e}\n{caption}",
                    parse_mode='HTML',
                    reply_markup=markup
                )
        else:
            await bot.send_message(
                message.chat.id,
                f"🖼 Нет превью\n{caption}",
                parse_mode='HTML',
                reply_markup=markup
            )
    # Пагинация
    pag_markup = build_pagination_keyboard(user_id, page, total)
    if pag_markup.keyboard:
        await bot.send_message(
            message.chat.id,
            f"Страница {page+1} из {max(1, (total-1)//AVATARS_PER_PAGE+1)}",
            reply_markup=pag_markup
        )
    await bot.send_message(
        message.chat.id,
        "Меню аватаров:",
        reply_markup=my_avatars_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data in ["avatars_prev", "avatars_next"])
async def handle_avatars_pagination(call):
    user_id = call.from_user.id
    page = get_avatar_page(user_id)
    avatars = get_avatars_index(user_id)
    total = len(avatars)
    max_page = max(0, (total - 1) // AVATARS_PER_PAGE)
    if call.data == "avatars_prev":
        page = max(0, page - 1)
    elif call.data == "avatars_next":
        page = min(max_page, page + 1)
    set_avatar_page(user_id, page)
    await my_avatars_menu(call.message, page=page)
    await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
async def photo_menu_entry(message: Message):
    set_state(message.from_user.id, "photo_menu")
    await bot.send_message(
        message.chat.id,
        "🖼 Работа с фото\n\nУлучшайте фото или создавайте ИИ-аватары.",
        reply_markup=photo_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "✨ Улучшить фото")
async def enhance_photo_entry(message: Message):
    await bot.send_message(
        message.chat.id,
        "Отправьте фото для улучшения качества ✨.",
        reply_markup=ReplyKeyboardRemove()
    )
    set_state(message.from_user.id, 'photo_enhance')


@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
async def ai_photographer_menu(message: Message):
    set_state(message.from_user.id, "ai_photographer")
    await bot.send_message(
        message.chat.id,
        "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
        reply_markup=ai_photographer_keyboard()
    )


def get_gender_emoji(gender):
    if gender == 'man':
        return '👨'
    if gender == 'woman':
        return '👩'
    return '🧑'

def format_status(status):
    if status == 'ready':
        return '✅ Готов'
    if status == 'pending':
        return '⏳ Обучается'
    if status == 'error':
        return '❌ Ошибка'
    return '—'

def format_date(dt_str):
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        return dt_str or '—'


def build_avatar_control_keyboard(avatar_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🗑", callback_data=f"avatar_delete_{avatar_id}"),
        InlineKeyboardButton("✏️", callback_data=f"avatar_rename_{avatar_id}"),
        InlineKeyboardButton("✨", callback_data=f"avatar_generate_{avatar_id}")
    )
    return markup


@bot.message_handler(func=lambda m: m.text == "🖼 Образы")
async def gallery_menu(message: Message):
    set_state(message.from_user.id, "gallery")
    await bot.send_message(
        message.chat.id,
        "Галерея доступных образов и стилей скоро будет доступна.",
        reply_markup=ai_photographer_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
async def universal_back_handler(message: Message):
    user_id = message.from_user.id
    state = get_state(user_id)
    if state == "photo_menu":
        set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Главное меню. Выберите действие:",
            reply_markup=main_menu_keyboard()
        )
    elif state == "ai_photographer":
        set_state(user_id, "photo_menu")
        await bot.send_message(
            message.chat.id,
            "🖼 Работа с фото\n\nУлучшайте фото или создавайте ИИ-аватары.",
            reply_markup=photo_menu_keyboard()
        )
    elif state in ["my_avatars", "gallery"]:
        set_state(user_id, "ai_photographer")
        await bot.send_message(
            message.chat.id,
            "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
            reply_markup=ai_photographer_keyboard()
        )
    else:
        set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Главное меню. Выберите действие:",
            reply_markup=main_menu_keyboard()
        )


# --- Callback-обработчик для удаления аватара с подтверждением ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('avatar_delete_confirm_'))
async def handle_avatar_delete_confirm(call):
    user_id = call.from_user.id
    logging.info(f"[DEBUG] handle_avatar_delete_confirm: user_id={user_id}, data={call.data}")
    try:
        if user_id not in user_session or not isinstance(user_session[user_id], dict):
            user_session[user_id] = {}
        # Удаляем все старые wizard-сообщения
        for mid in user_session[user_id].get('wizard_message_ids', []):
            try:
                await bot.delete_message(call.message.chat.id, mid)
            except Exception as e:
                logging.error(f"[DEBUG] Ошибка удаления wizard-сообщения: {e}\n{traceback.format_exc()}")
        user_session[user_id]['wizard_message_ids'] = []
        user_session[user_id]['avatar_delete_wizard_active'] = False
        avatar_id = call.data.split('_')[-1]
        logging.info(f"[DEBUG] До clear_avatar_fsm: user_id={user_id}, avatar_id={avatar_id}")
        clear_avatar_fsm(user_id, avatar_id)
        logging.info(f"[DEBUG] После clear_avatar_fsm: user_id={user_id}, avatar_id={avatar_id}")
        avatars = get_avatars_index(user_id)
        logging.info(f"[DEBUG] После удаления, get_avatars_index: {avatars}")
        await bot.send_message(call.message.chat.id, "Аватар удалён.")
        await my_avatars_menu(call.message)
        await bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"[DEBUG] Ошибка в handle_avatar_delete_confirm: {e}\n{traceback.format_exc()}")

@bot.callback_query_handler(func=lambda call: call.data == 'avatar_delete_cancel')
async def handle_avatar_delete_cancel(call):
    user_id = call.from_user.id
    logging.info(f"[DEBUG] handle_avatar_delete_cancel: user_id={user_id}, data={call.data}")
    try:
        if user_id not in user_session or not isinstance(user_session[user_id], dict):
            user_session[user_id] = {}
        # Удаляем все старые wizard-сообщения
        for mid in user_session[user_id].get('wizard_message_ids', []):
            try:
                await bot.delete_message(call.message.chat.id, mid)
            except Exception as e:
                logging.error(f"[DEBUG] Ошибка удаления wizard-сообщения: {e}\n{traceback.format_exc()}")
        user_session[user_id]['wizard_message_ids'] = []
        user_session[user_id]['avatar_delete_wizard_active'] = False
        await bot.send_message(call.message.chat.id, "Удаление отменено.")
        await bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"[DEBUG] Ошибка в handle_avatar_delete_cancel: {e}\n{traceback.format_exc()}")

@bot.callback_query_handler(
    func=lambda call: call.data.startswith('avatar_delete_')
    and not call.data.startswith('avatar_delete_confirm_')
    and call.data != 'avatar_delete_cancel'
)
async def handle_avatar_delete(call):
    user_id = call.from_user.id
    logging.info(f"[DEBUG] handle_avatar_delete: user_id={user_id}, data={call.data}")
    try:
        if user_id not in user_session or not isinstance(user_session[user_id], dict):
            user_session[user_id] = {}
        # Проверка: если wizard уже активен, не открываем новый
        if user_session[user_id].get('avatar_delete_wizard_active'):
            await bot.answer_callback_query(call.id, "Подтверждение уже открыто.")
            return
        user_session[user_id]['avatar_delete_wizard_active'] = True
        # Удаляем все старые wizard-сообщения
        for mid in user_session[user_id].get('wizard_message_ids', []):
            try:
                await bot.delete_message(call.message.chat.id, mid)
            except Exception as e:
                logging.error(f"[DEBUG] Ошибка удаления wizard-сообщения: {e}\n{traceback.format_exc()}")
        user_session[user_id]['wizard_message_ids'] = []
        avatar_id = call.data.split('_')[-1]
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Да, удалить", callback_data=f"avatar_delete_confirm_{avatar_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data="avatar_delete_cancel")
        )
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        msg = await bot.send_message(
            call.message.chat.id,
            f"Вы уверены, что хотите удалить этот аватар? Это действие необратимо.",
            reply_markup=markup
        )
        user_session[user_id]['wizard_message_ids'] = [msg.message_id]
        await bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"[DEBUG] Ошибка в handle_avatar_delete: {e}\n{traceback.format_exc()}")

# --- Callback-обработчик для переименования аватара ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('avatar_rename_'))
async def handle_avatar_rename(call):
    avatar_id = call.data.split('_')[-1]
    user_id = call.from_user.id
    from frontend_bot.services.state_manager import set_state
    set_state(user_id, f"avatar_rename_{avatar_id}")
    await bot.send_message(call.message.chat.id, "Введите новое имя для аватара:")
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text and m.text.strip() and get_state(m.from_user.id) and get_state(m.from_user.id).startswith('avatar_rename_'))
async def handle_avatar_rename_text(message: Message):
    user_id = message.from_user.id
    state = get_state(user_id)
    avatar_id = state.split('_')[-1]
    new_title = message.text.strip()
    update_avatar_fsm(user_id, avatar_id, title=new_title)
    from frontend_bot.services.state_manager import set_state
    set_state(user_id, "my_avatars")
    await bot.send_message(message.chat.id, f"Имя аватара обновлено на: <b>{new_title}</b>", parse_mode='HTML')
    await my_avatars_menu(message)

# --- Callback-обработчик для генерации образа (заглушка) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('avatar_generate_'))
async def handle_avatar_generate(call):
    await bot.send_message(call.message.chat.id, "Функция генерации образа в разработке. Ожидайте обновлений!")
    await bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text == "👁 Просмотреть аватары")
async def view_avatars_handler(message: Message):
    await my_avatars_menu(message) 