from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.main import get_main_menu
from app.core.di import get_user_service
from app.services.user import UserService
from app.core.logger import get_logger
from app.core.static_resources import StaticResources

logger = get_logger(__name__)
router = Router()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Автоматически регистрирует пользователя и показывает приветственное сообщение с фото Аиши.
    """
    await state.clear()
    
    try:
        # Автоматическая регистрация пользователя
        telegram_user_data = {
            "id": message.from_user.id,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
            "language_code": message.from_user.language_code,
            "is_premium": getattr(message.from_user, 'is_premium', False),
            "is_bot": message.from_user.is_bot,
        }
        
        async with get_user_service() as user_service:
            user = await user_service.register_user(telegram_user_data)
            if not user:
                logger.error(f"Не удалось зарегистрировать пользователя {message.from_user.id}")
                # Всё равно показываем приветственное сообщение
        
        # Приветственное сообщение с фото Аиши
        welcome_text = f"""👋 Привет, {message.from_user.first_name}!

🤖 Я Aisha - ваш персональный ИИ-помощник для создания уникальных изображений и контента!

✨ **Что я умею:**

🎭 **Создание аватаров**
• Обучаю персональные модели на ваших фото
• Создаю профессиональные портреты
• Генерирую изображения в любом стиле

🎨 **Генерация изображений** 
• Реалистичные фотографии
• Художественные стили
• Креативные концепты

🖼️ **Личная галерея**
• Сохраняю всю историю генераций
• Удобный просмотр и управление
• Экспорт в высоком качестве

🎤 **Транскрибация**
• Аудио в текст на русском и английском
• Высокая точность распознавания
• Поддержка различных форматов

💎 **Доверьтесь профессионалу!**
Я создаю изображения студийного качества, которые поразят ваших друзей и коллег!

🚀 **Готовы начать творить?** Выберите действие в меню ниже!"""

        # Путь к аватару Аиши
        avatar_path = StaticResources.get_aisha_avatar_path()
        
        if avatar_path.exists():
            # Отправляем фото с подписью
            photo = FSInputFile(avatar_path)
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        else:
            # Если фото нет, отправляем только текст
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        # Fallback на упрощенное сообщение
        logger.exception(f"Ошибка в команде /start: {e}")
        try:
            fallback_text = f"""👋 Привет, {message.from_user.first_name}! 

🤖 Я Aisha Bot - ваш персональный помощник для создания изображений с ИИ.

✨ Готовы создавать уникальные изображения? Выберите действие в меню!"""
            
            await message.answer(
                fallback_text,
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
    Показывает справку - ИСПРАВЛЕНО: устранены ошибки Markdown парсинга
    """
    # ✅ ИСПРАВЛЕННЫЙ текст справки с корректным форматированием
    help_text = """❓ **Справка по боту**

🎨 **Создание изображений:**
• Выберите 'Создать изображение'
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

📞 **Поддержка:** @aisha_support_bot"""

    try:
        # ✅ Улучшенная обработка с правильным fallback'ом
        await call.message.edit_text(
            help_text,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        await call.answer()
        
    except TelegramBadRequest as telegram_error:
        error_msg = str(telegram_error).lower()
        
        if "parse entities" in error_msg:
            # Проблема с Markdown - используем HTML
            logger.warning(f"Markdown ошибка в справке, переходим на HTML: {telegram_error}")
            
            help_text_html = """❓ <b>Справка по боту</b>

🎨 <b>Создание изображений:</b>
• Выберите 'Создать изображение'
• Выберите стиль из галереи или введите свой промпт
• Дождитесь генерации (30-90 секунд)

🎭 <b>Аватары:</b>
• Создайте персональный аватар из ваших фото
• Портретные аватары - для реалистичных изображений
• Стилевые аватары - для художественных образов

🖼️ <b>Галерея:</b>
• Просматривайте историю генераций
• Сохраняйте избранные изображения
• Делитесь результатами

💡 <b>Советы:</b>
• Загружайте качественные фото для аватаров
• Используйте детальные описания в промптах
• Экспериментируйте с разными стилями

📞 <b>Поддержка:</b> @aisha_support_bot"""
            
            try:
                await call.message.edit_text(
                    help_text_html,
                    reply_markup=get_main_menu(),
                    parse_mode="HTML"
                )
                await call.answer()
                
            except TelegramBadRequest as html_error:
                # HTML тоже не работает - отправляем без форматирования
                logger.warning(f"HTML ошибка в справке, убираем форматирование: {html_error}")
                
                help_text_plain = """❓ Справка по боту

🎨 Создание изображений:
• Выберите 'Создать изображение'
• Выберите стиль из галереи или введите свой промпт
• Дождитесь генерации (30-90 секунд)

🎭 Аватары:
• Создайте персональный аватар из ваших фото
• Портретные аватары - для реалистичных изображений
• Стилевые аватары - для художественных образов

🖼️ Галерея:
• Просматривайте историю генераций
• Сохраняйте избранные изображения
• Делитесь результатами

💡 Советы:
• Загружайте качественные фото для аватаров
• Используйте детальные описания в промптах
• Экспериментируйте с разными стилями

📞 Поддержка: @aisha_support_bot"""
                
                try:
                    await call.message.edit_text(
                        help_text_plain,
                        reply_markup=get_main_menu(),
                        parse_mode=None
                    )
                    await call.answer()
                    
                except TelegramBadRequest as final_error:
                    # Редактирование не работает - отправляем новое сообщение
                    logger.warning(f"Не можем редактировать сообщение, отправляем новое: {final_error}")
                    await call.message.answer(
                        help_text_plain,
                        reply_markup=get_main_menu(),
                        parse_mode=None
                    )
                    await call.answer()
                    
        elif "message is not modified" in error_msg:
            # Контент уже такой же - просто отвечаем
            await call.answer("ℹ️ Справка уже отображена", show_alert=False)
            
        elif "message to delete not found" in error_msg:
            # Сообщение уже удалено - отправляем новое
            logger.warning(f"Сообщение для удаления не найдено: {telegram_error}")
            await call.message.answer(
                help_text.replace('**', '').replace('*', ''),
                reply_markup=get_main_menu(),
                parse_mode=None
            )
            await call.answer()
            
        else:
            # Другая ошибка Telegram
            logger.error(f"Неожиданная Telegram ошибка в справке: {telegram_error}")
            await call.answer("❌ Ошибка отображения справки", show_alert=True)
                
    except Exception as general_error:
        # Любая другая ошибка
        logger.exception(f"Критическая ошибка в справке: {general_error}")
        try:
            # Попытка отправить упрощенное сообщение
            await call.message.answer(
                "❓ Справка по боту\n\nВыберите нужный раздел в главном меню.\n\nПоддержка: @aisha_support_bot",
                reply_markup=get_main_menu(),
                parse_mode=None
            )
            await call.answer()
        except Exception:
            # Финальный fallback
            await call.answer("❌ Произошла ошибка при загрузке справки", show_alert=True)

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

@router.callback_query(F.data == "main_generation")
async def show_main_generation(call: CallbackQuery, state: FSMContext):
    """
    Обработчик кнопки "Генерация" - перенаправляет на модуль генерации
    """
    try:
        # Импортируем обработчик генерации
        from app.handlers.generation.main_handler import generation_handler
        
        # Очищаем состояние
        await state.clear()
        
        # Вызываем метод обработчика генерации
        await generation_handler.show_generation_menu(call)
        
        logger.info(f"Пользователь {call.from_user.id} перешел к генерации изображений")
        
    except Exception as e:
        logger.exception(f"Ошибка при переходе к генерации: {e}")
        await call.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "styles_menu")
async def show_styles_menu(call: CallbackQuery):
    """
    Обработчик кнопки "Стили" - заглушка с информацией о разработке
    """
    try:
        await call.answer(
            "🎭 Библиотека стилей\n\n"
            "🚧 В разработке\n\n"
            "📅 Скоро:\n"
            "• Готовые стили\n"
            "• Художественные фильтры\n"
            "• Тематические коллекции\n\n"
            "💡 Используйте 'Аватары' для создания изображений!", 
            show_alert=True
        )
        
        logger.info(f"Пользователь {call.from_user.id} попытался зайти в стили (заглушка)")
        
    except Exception as e:
        logger.exception(f"Ошибка в обработчике стилей: {e}")
        await call.answer("❌ Произошла ошибка", show_alert=True) 