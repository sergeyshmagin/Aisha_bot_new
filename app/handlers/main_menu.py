from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

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

    try:
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu()
        )
    except Exception as e:
        # Fallback на упрощенное сообщение
        logger.exception(f"Ошибка стартового сообщения: {e}")
        try:
            await message.answer(
                f"👋 Привет, {message.from_user.first_name}! Добро пожаловать в Aisha Bot!",
                reply_markup=get_main_menu()
            )
        except Exception as final_error:
            logger.exception(f"Критическая ошибка стартового сообщения: {final_error}")

@router.callback_query(F.data == "main_menu")
async def show_main_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает главное меню БЕЗ создания новых сообщений.
    """
    await state.clear()
    
    menu_text = "🏠 **Главное меню**\n\nВыберите действие:"
    
    try:
        if call.message.photo:
            # ✅ ИСПРАВЛЕНИЕ: Если сообщение с фото - редактируем подпись
            await call.message.edit_caption(
                caption=menu_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            logger.debug("✅ Главное меню: отредактирована подпись фото")
            
        elif call.message.text or call.message.caption:
            # ✅ Обычное текстовое сообщение - редактируем текст
            await call.message.edit_text(
                menu_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            logger.debug("✅ Главное меню: отредактирован текст")
            
        else:
            # ❌ Неизвестный тип сообщения - отправляем новое (крайний случай)
            await call.message.answer(
                menu_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            logger.debug("⚠️ Главное меню: отправлено новое сообщение (неизвестный тип)")
            
    except TelegramBadRequest as markdown_error:
        if "parse entities" in str(markdown_error):
            # Проблема с Markdown - повторяем без форматирования
            menu_text_plain = "🏠 Главное меню\n\nВыберите действие:"
            
            try:
                if call.message.photo:
                    await call.message.edit_caption(
                        caption=menu_text_plain,
                        reply_markup=get_main_menu()
                    )
                elif call.message.text or call.message.caption:
                    await call.message.edit_text(
                        menu_text_plain,
                        reply_markup=get_main_menu()
                    )
                else:
                    await call.message.answer(
                        menu_text_plain,
                        reply_markup=get_main_menu()
                    )
            except Exception as fallback_error:
                logger.exception(f"Критическая ошибка при fallback главного меню: {fallback_error}")
                await call.answer("❌ Ошибка главного меню", show_alert=True)
                
        elif "there is no text in the message to edit" in str(markdown_error):
            # Нет текста для редактирования - пробуем edit_caption
            try:
                await call.message.edit_caption(
                    caption=menu_text.replace('**', ''),
                    reply_markup=get_main_menu()
                )
            except Exception:
                # Если и это не работает - отправляем новое
                await call.message.answer(
                    menu_text.replace('**', ''),
                    reply_markup=get_main_menu()
                )
                
        else:
            # Другая ошибка Telegram
            logger.warning(f"Telegram ошибка в главном меню: {markdown_error}")
            try:
                await call.message.answer(
                    "🏠 Главное меню\n\nВыберите действие:",
                    reply_markup=get_main_menu()
                )
            except Exception:
                await call.answer("❌ Ошибка загрузки меню", show_alert=True)
                
    except Exception as general_error:
        logger.exception(f"Общая ошибка в главном меню: {general_error}")
        try:
            await call.message.answer(
                "🏠 Главное меню\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        except Exception:
            await call.answer("❌ Произошла ошибка", show_alert=True)
    
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
async def show_my_gallery(call: CallbackQuery, state: FSMContext):
    """
    Показывает персональную галерею пользователя.
    """
    # Импортируем обработчик галереи
    from app.handlers.gallery import gallery_handler
    
    # Очищаем состояние
    await state.clear()
    
    # Вызываем метод нового обработчика галереи
    await gallery_handler.gallery_viewer.show_gallery_main(call, state)

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
        
        # Уровень 1: Попытка с HTML
        try:
            await call.message.edit_text(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except TelegramBadRequest as html_error:
            if "parse entities" in str(html_error):
                # Уровень 2: Проблема с HTML парсингом - отправляем без форматирования
                logger.warning(f"Проблема с HTML парсингом в меню транскрибации: {html_error}")
                await call.message.edit_text(
                    "🎙 Транскрибация\n\nВыберите действие:",
                    parse_mode=None,
                    reply_markup=builder.as_markup()
                )
            else:
                # Другая ошибка - fallback
                logger.exception(f"Другая ошибка в меню транскрибации: {html_error}")
                await call.message.answer(
                    "🎙 Транскрибация\n\nВыберите действие:",
                    parse_mode=None,
                    reply_markup=builder.as_markup()
                )
        
    except Exception as e:
        logger.exception(f"Критическая ошибка при показе меню транскрибации: {e}")
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

    try:
        # ✅ Проверяем тип сообщения перед редактированием
        if call.message.photo:
            # Сообщение с фото - удаляем и отправляем новое текстовое
            await call.message.delete()
            await call.message.answer(
                help_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            logger.debug("✅ show_help: удалено фото, отправлен новый текст")
            return
            
        # Обычное текстовое сообщение - пробуем редактировать
        await call.message.edit_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
    except TelegramBadRequest as markdown_error:
        if "parse entities" in str(markdown_error):
            # Уровень 2: Проблема с парсингом Markdown - отправляем без форматирования
            logger.warning(f"Проблема с Markdown парсингом в справке: {markdown_error}")
            
            # Убираем Markdown символы из текста
            help_text_plain = help_text.replace('**', '').replace('*', '')
            
            try:
                if call.message.photo:
                    # Для фото - удаляем и отправляем новое
                    await call.message.delete()
                    await call.message.answer(
                        help_text_plain,
                        reply_markup=get_main_menu(),
                        parse_mode=None
                    )
                else:
                    # Для текста - редактируем
                    await call.message.edit_text(
                        help_text_plain,
                        reply_markup=get_main_menu(),
                        parse_mode=None
                    )
                    
            except TelegramBadRequest as edit_error:
                if "there is no text in the message to edit" in str(edit_error):
                    # Finall fallback - отправляем новое сообщение
                    logger.warning(f"Fallback: отправляем новое сообщение в справке: {edit_error}")
                    await call.message.answer(
                        help_text_plain,
                        reply_markup=get_main_menu(),
                        parse_mode=None
                    )
                else:
                    logger.exception(f"Критическая ошибка при fallback справке: {edit_error}")
                    await call.answer("❌ Ошибка отображения справки", show_alert=True)
                    
        else:
            # Другая ошибка Telegram - всегда отправляем новое сообщение
            logger.exception(f"Ошибка Telegram при отправке справки: {markdown_error}")
            help_text_plain = help_text.replace('**', '').replace('*', '')
            try:
                await call.message.answer(
                    help_text_plain,
                    reply_markup=get_main_menu(),
                    parse_mode=None
                )
            except Exception:
                await call.answer("❌ Ошибка загрузки справки", show_alert=True)
                
    except Exception as general_error:
        # Общая ошибка - финальный fallback
        logger.exception(f"Общая ошибка в функции справки: {general_error}")
        help_text_plain = help_text.replace('**', '').replace('*', '')
        try:
            await call.message.answer(
                help_text_plain,
                reply_markup=get_main_menu(),
                parse_mode=None
            )
        except Exception:
            await call.answer("❌ Произошла ошибка", show_alert=True)

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
    Возвращает в главное меню БЕЗ создания новых сообщений.
    """
    await call.answer("🔄 Возврат в главное меню...", show_alert=False)
    
    menu_text = "🏠 Главное меню\n\nВыберите действие:"
    
    try:
        if call.message.photo:
            # ✅ Если сообщение с фото - редактируем подпись
            await call.message.edit_caption(
                caption=menu_text,
                reply_markup=get_main_menu()
            )
            logger.debug("✅ back_to_main: отредактирована подпись фото")
            
        elif call.message.text or call.message.caption:
            # ✅ Обычное текстовое сообщение - редактируем текст  
            await call.message.edit_text(
                menu_text,
                reply_markup=get_main_menu()
            )
            logger.debug("✅ back_to_main: отредактирован текст")
            
        else:
            # ❌ Неизвестный тип - отправляем новое (крайний случай)
            await call.message.answer(
                menu_text,
                reply_markup=get_main_menu()
            )
            logger.debug("⚠️ back_to_main: отправлено новое сообщение")
            
    except TelegramBadRequest as edit_error:
        # Не удалось редактировать - fallback стратегии
        logger.warning(f"Не удалось редактировать в back_to_main: {edit_error}")
        
        try:
            if "there is no text in the message to edit" in str(edit_error):
                # Пробуем edit_caption для фото
                await call.message.edit_caption(
                    caption=menu_text,
                    reply_markup=get_main_menu()
                )
            else:
                # Другая ошибка - отправляем новое сообщение
                await call.message.answer(
                    menu_text,
                    reply_markup=get_main_menu()
                )
        except Exception as send_error:
            logger.exception(f"Критическая ошибка в back_to_main: {send_error}")
            await call.answer("❌ Ошибка возврата в меню", show_alert=True)
            
    except Exception as general_error:
        logger.exception(f"Общая ошибка в back_to_main: {general_error}")
        try:
            await call.message.answer(
                menu_text,
                reply_markup=get_main_menu()
            )
        except Exception:
            await call.answer("❌ Ошибка главного меню", show_alert=True) 