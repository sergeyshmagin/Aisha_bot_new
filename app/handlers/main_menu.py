from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.keyboards.main import get_main_menu
from app.core.di import get_user_service
from app.services.user import UserService
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    """
    await state.clear()
    
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

🤖 Я Aisha Bot - ваш персональный помощник для создания изображений с ИИ.

✨ **Что я умею:**
• 🎨 Создавать изображения с вашими аватарами
• 🎭 Обучать персональные аватары
• 🖼️ Сохранять историю ваших генераций
• 🎤 Транскрибировать аудио и видео

🚀 Выберите действие в меню ниже!"""

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "main_menu")
async def show_main_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает главное меню.
    """
    await state.clear()
    
    try:
        await call.message.edit_text(
            "🏠 **Главное меню**\n\nВыберите действие:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        # Если не можем редактировать сообщение, отправляем новое
        logger.debug(f"Не удалось редактировать сообщение: {e}")
        await call.message.answer(
            "🏠 **Главное меню**\n\nВыберите действие:",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    
    await call.answer()

@router.callback_query(F.data == "avatar_menu")
async def show_avatar_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню аватаров - перенаправляет на правильный обработчик.
    """
    # Импортируем новый обработчик аватаров
    from app.handlers.avatar import avatar_main_handler
    
    # Вызываем метод нового обработчика
    await avatar_main_handler.show_avatar_menu(call, state)

@router.callback_query(F.data == "my_gallery")
async def show_my_gallery(call: CallbackQuery):
    """
    Показывает персональную галерею пользователя.
    """
    await call.answer("🔄 Переход в галерею...", show_alert=False)
    
    # TODO: Реализовать персональную галерею
    await call.message.edit_text(
        "🖼️ **Моя галерея**\n\n🚧 Раздел в разработке...\n\nЗдесь будет:\n• История ваших генераций\n• Избранные изображения\n• Статистика\n• Поиск и фильтры",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "transcribe_menu")
async def show_transcribe_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню транскрибации - перенаправляет на правильный обработчик.
    """
    await call.answer("🔄 Переход к транскрибации...", show_alert=False)
    
    # Импортируем и используем настоящий обработчик транскрибации
    from app.handlers import transcript_main_handler
    
    # Используем метод обработчика для показа меню через call.message
    try:
        await state.set_state(None)  # Очищаем состояние
        
        # Создаем клавиатуру транскрибации
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🎤 Аудио", callback_data="transcribe_audio"),
            InlineKeyboardButton(text="📝 Текст", callback_data="transcribe_text")
        )
        builder.row(InlineKeyboardButton(text="📜 История", callback_data="transcribe_history"))
        builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
        
        await call.message.edit_text(
            "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при показе меню транскрибации: {e}")
        await call.answer("❌ Ошибка при загрузке меню транскрибации", show_alert=True)

@router.callback_query(F.data == "main_help")
async def show_help(call: CallbackQuery):
    """
    Показывает справку.
    """
    help_text = """❓ **Справка по боту**

🎨 **Создание изображений:**
• Выберите "🎨 Создать изображение"
• Выберите стиль из галереи или введите свой промпт
• Дождитесь генерации (30-90 секунд)

🎭 **Аватары:**
• Создайте персональный аватар из ваших фото
• Портретные аватары - для реалистичных изображений
• Стилевые аватары - для художественных образов

🖼️ **Галерея:**
• Просматривайте историю генераций
• Сохраняйте избранные изображения
• Делитесь результатами

💡 **Советы:**
• Загружайте качественные фото для аватаров
• Используйте детальные описания в промптах
• Экспериментируйте с разными стилями

📞 **Поддержка:** @support_username"""

    await call.message.edit_text(
        help_text,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("balance_details_"))
async def show_balance_details(call: CallbackQuery):
    """
    Показывает детальную информацию о пополнении баланса во всплывающем окне.
    """
    try:
        # Парсим данные из callback_data: balance_details_{added_amount}_{current_balance}
        parts = call.data.split("_")
        if len(parts) >= 4:
            added_amount = float(parts[2])
            current_balance = float(parts[3])
            
            # Формируем детальное сообщение
            details_text = (
                f"💰 Детали пополнения баланса:\n\n"
                f"➕ Пополнено: {added_amount} кредитов\n"
                f"💎 Текущий баланс: {current_balance} кредитов\n\n"
                f"🎯 Что можно сделать:\n"
                f"• Создать аватар (120-150 кредитов)\n"
                f"• Генерировать изображения\n"
                f"• Обрабатывать аудио\n\n"
                f"✨ Спасибо за использование нашего сервиса!"
            )
            
            await call.answer(details_text, show_alert=True)
            logger.info(f"Показаны детали пополнения пользователю {call.from_user.id}: +{added_amount}, баланс: {current_balance}")
        else:
            await call.answer("❌ Ошибка в данных пополнения", show_alert=True)
            
    except Exception as e:
        logger.exception(f"Ошибка при показе деталей баланса: {e}")
        await call.answer("❌ Ошибка при получении информации о балансе", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    """
    Возвращает в главное меню.
    """
    await call.answer("🔄 Возврат в главное меню...", show_alert=False)
    
    try:
        await call.message.edit_text(
            "👋 Главное меню\n\nВыберите действие:",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        # Если не можем редактировать сообщение, отправляем новое
        logger.debug(f"Не удалось редактировать сообщение в back_to_main: {e}")
        await call.message.answer(
            "👋 Главное меню\n\nВыберите действие:",
            reply_markup=get_main_menu()
        ) 