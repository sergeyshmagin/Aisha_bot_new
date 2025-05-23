from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.keyboards.main import get_main_menu
from app.keyboards.gallery import get_gallery_menu
from app.core.di import get_user_service
from app.services.user import UserService
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Регистрирует пользователя и показывает главное меню.
    """
    try:
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                user_data = {
                    "id": message.from_user.id,
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                    "last_name": message.from_user.last_name,
                    "language_code": message.from_user.language_code or "ru",
                    "is_bot": message.from_user.is_bot,
                    "is_premium": getattr(message.from_user, "is_premium", False)
                }
                user = await user_service.register_user(user_data)
                if user:
                    logger.info(f"Создан новый пользователь: {user.telegram_id}")
                else:
                    logger.error("Не удалось создать пользователя")
                    await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")
                    return
            
            await message.answer(
                "👋 Добро пожаловать! Выберите действие:",
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.exception("Ошибка при регистрации пользователя")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже или обратитесь в поддержку."
        )

@router.callback_query(F.data == "main_help")
async def show_help(call: CallbackQuery):
    """
    Показывает всплывающее окно с помощью.
    """
    help_text = (
        "ℹ️ Помощь по использованию бота:\n\n"
        "🎤 Транскрибация — обработка аудио и .txt\n"
        "🖼 Галерея — просмотр и управление изображениями\n"
        "🧑‍🎨 Аватары — создание и управление аватарами\n\n"
        "Для возврата в главное меню используйте команду /start"
    )
    await call.answer(help_text, show_alert=True)

@router.callback_query(F.data == "business_gallery")
async def show_gallery(call: CallbackQuery):
    """
    Показывает галерею.
    """
    await call.answer("🔄 Переход в галерею...", show_alert=False)
    await call.message.edit_text(
        "🖼 Галерея\n\nВыберите действие:",
        reply_markup=get_gallery_menu()
    )

@router.callback_query(F.data == "business_avatar")
async def show_avatar_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню аватаров - перенаправляет на правильный обработчик.
    """
    # Импортируем новый обработчик аватаров
    from app.handlers.avatar import avatar_main_handler
    
    # Вызываем метод нового обработчика
    await avatar_main_handler.show_avatar_menu(call, state)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    """
    Возвращает в главное меню.
    """
    await call.answer("🔄 Возврат в главное меню...", show_alert=False)
    await call.message.edit_text(
        "👋 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "transcribe_menu")
async def show_transcribe_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню транскрибации (обработка аудио и текста).
    """
    from app.handlers.transcript_main import TranscriptMainHandler
    handler = TranscriptMainHandler()
    await handler._handle_transcribe_command(call.message, state) 