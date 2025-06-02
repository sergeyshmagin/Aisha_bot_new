from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from app.keyboards.main import get_main_menu
from app.core.logger import get_logger

logger = get_logger(__name__)
fallback_router = Router()

@fallback_router.callback_query(F.data.startswith("business_") | F.data.startswith("old_"))
async def fallback_callback(call: CallbackQuery):
    await call.answer("Это действие устарело. Пожалуйста, используйте новое меню.", show_alert=True)

@fallback_router.callback_query()
async def fallback_unknown_callback(call: CallbackQuery):
    """Обработчик для всех необработанных callback queries"""
    logger.warning(f"Необработанный callback: {call.data} от пользователя {call.from_user.id}")
    await call.answer("❌ Неизвестная команда. Используйте кнопки меню.", show_alert=True)

@fallback_router.message()
async def fallback_unknown_message(message: Message, state: FSMContext):
    """Обработчик для всех необработанных сообщений"""
    logger.warning(f"Необработанное сообщение: '{message.text}' от пользователя {message.from_user.id}")
    
    # Отправляем главное меню
    await message.answer(
        "❓ Я не понимаю эту команду.\n\n"
        "Используйте кнопки меню ниже или команду /start:",
        reply_markup=get_main_menu()
    )
