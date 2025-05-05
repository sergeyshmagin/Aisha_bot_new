from telebot.types import Message, ReplyKeyboardRemove
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import set_state, get_state
from frontend_bot.keyboards.reply import (
    photo_menu_keyboard, ai_photographer_keyboard,
    my_avatars_keyboard, build_avatars_keyboard
)
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.services.avatar_manager import get_avatars_index


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


@bot.message_handler(func=lambda m: m.text == "🖼 Мои аватары")
async def my_avatars_menu(message: Message):
    set_state(message.from_user.id, "my_avatars")
    user_id = message.from_user.id
    avatars = get_avatars_index(user_id)
    if not avatars:
        await bot.send_message(
            message.chat.id,
            "Пока у вас нет аватаров. Создайте первый! 🚀",
            reply_markup=my_avatars_keyboard()
        )
    else:
        await bot.send_message(
            message.chat.id,
            "Меню аватаров:",
            reply_markup=await build_avatars_keyboard(avatars)
        )


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