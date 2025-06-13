"""
Обработчики главного меню бота
"""
from typing import Optional, Dict, Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.main import (
    get_main_menu, get_ai_creativity_menu, get_images_menu, get_video_menu, 
    get_news_menu, get_my_projects_menu, get_avatar_generation_menu, 
    get_gallery_menu, get_business_menu, get_tasks_menu, get_add_to_chat_menu,
    get_quick_action_menu
)
from app.core.di import get_user_service
from app.services.user import UserService
from app.core.logger import get_logger
from app.core.static_resources import StaticResources
from app.shared.handlers.base_handler import BaseHandler

# Импортируем функцию создания аватара напрямую
from app.handlers.avatar.create import start_avatar_creation
# Импортируем обработчик генерации
from app.handlers.generation.main_handler import GenerationMainHandler

logger = get_logger(__name__)
router = Router()

# Создаем экземпляр базового обработчика
base_handler = BaseHandler()

# Создаем экземпляр обработчика генерации
generation_handler = GenerationMainHandler()

# Регистрируем обработчик создания аватара
@router.callback_query(F.data == "avatar_create")
async def handle_avatar_create(call: CallbackQuery, state: FSMContext):
    """
    🎭 Создать аватар - подключаем к существующему обработчику
    """
    await start_avatar_creation(call, state)

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

🤖 Я Aisha - помогу вам создавать красивые фотографии и видео!

✨ **Что вы сможете делать:**

📷 **Создание фотографий**
• Создавать красивые фото
• Создать красивые картинки для соцсетей
• Попробовать себя в разных образах и стилях

🎬 **Создание видео** 
• Оживить ваши фотографии
• Сделать говорящие портреты
• Создать креативные ролики

📂 **Личная галерея**
• Все ваши работы сохраняются автоматически
• Удобный просмотр и управление
• Можно поделиться с друзьями

📝 **Помощник для работы**
• Превратить голосовые сообщения в текст
• Следить за новостями и трендами
• Управлять рабочими задачами

💎 **Всё просто и понятно!**
Не нужно разбираться в технологиях - просто выбирайте что хотите и получайте результат!

🚀 **Готовы начать?** Выберите что вас интересует!"""

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

@router.callback_query(F.data == "ai_creativity_menu")
async def show_ai_creativity_menu(call: CallbackQuery, state: FSMContext):
    """
    🎨 **Творчество**

🚀 **Создавайте красивый контент:**

📷 **Фото** - сделайте профессиональные снимки с вашим лицом или создайте художественные картинки
🎬 **Видео** - оживите фотографии и создайте креативные ролики
📂 **Мои работы** - просматривайте всё что создали

💡 **Все ваши работы сохраняются автоматически в высоком качестве**

Что будем создавать?"""

    await state.clear()
    
    menu_text = """🎨 **Творчество**

🚀 **Создавайте красивый контент:**

📷 **Фото** - сделайте профессиональные снимки с вашим лицом или создайте художественные картинки
🎬 **Видео** - оживите фотографии и создайте креативные ролики
📂 **Мои работы** - просматривайте всё что создали

💡 **Все ваши работы сохраняются автоматически в высоком качестве**

Что будем создавать?"""

    try:
        await base_handler.safe_edit_message(
            call,
            menu_text,
            reply_markup=get_ai_creativity_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню творчества: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "images_menu")
async def show_images_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню создания изображений.
    """
    await state.clear()
    
    menu_text = """📷 **Фото**

🎭 **Доступные технологии:**

📷 **Фото со мной** - используйте обученную на ваших фото модель
📝 **По описанию** - создание любых картинок через Imagen 4
🎬 **Видео** - создание видеороликов (скоро)

💡 **Создавайте профессиональные снимки и художественные работы**

Что выберете?"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_images_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню изображений: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "video_generation_stub")
async def show_video_generation_stub(call: CallbackQuery, state: FSMContext):
    """
    Заглушка для генерации видео
    """
    await state.clear()
    
    stub_text = """🎬 **Видео генерация**

🚧 **В разработке**

Скоро здесь будут доступны:
• 🎭 Hedra AI - анимация лиц
• 🌟 Kling - создание видео по тексту
• 🎪 Weo3 - профессиональные ролики

📅 **Ожидаемый запуск:** В ближайших обновлениях

💡 **Пока что вы можете:**
• Создавать изображения с вашим образом
• Генерировать картинки по описанию"""

    try:
        await call.message.edit_text(
            stub_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data="images_menu"
                    ),
                    InlineKeyboardButton(
                        text="🏠 Главное меню",
                        callback_data="main_menu"
                    )
                ]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка заглушки видео: {e}")
        await call.answer("❌ Ошибка загрузки", show_alert=True)

@router.callback_query(F.data == "avatar_generation_menu")
async def show_avatar_generation_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню генерации с аватаром.
    """
    await state.clear()
    
    menu_text = """📷 **Фото со мной**

🎭 **Создавайте фото с вашим лицом:**

✍️ **Свой промпт** - опишите желаемую сцену
📷 **Генерация по фото** - загрузите референс для копирования стиля
🎨 **Выбрать стиль** - используйте готовые художественные стили

💡 **Для работы нужен обученный аватар**

Выберите способ создания:"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_avatar_generation_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню аватара: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "video_menu")
async def show_video_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню создания видео.
    """
    await state.clear()
    
    menu_text = """🎬 **Создание видео**

🚀 **Передовые AI технологии:**

🎭 **Hedra AI** - создавайте говорящие портреты из фотографий
🌟 **Kling 2.1 Pro** - кинематографическое качество, до 10 секунд
🎪 **Weo3 Creative** - креативные эффекты и трансформации

📹 **Или просмотрите уже созданные видео**

💡 **Совет:** Для лучшего качества используйте четкие фотографии и детальные промпты

Выберите технологию:"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_video_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню видео: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "audio_menu")
async def show_audio_menu(call: CallbackQuery, state: FSMContext):
    """
    Показывает меню аудио и речи.
    """
    await state.clear()
    
    menu_text = """🔊 **Аудио и речь**

🎙️ **Доступные функции:**

🎤 **Транскрибация** - преобразование аудио в текст (OpenAI Whisper)
🗣️ **TTS Озвучка** - создание речи из текста (скоро)
🎵 **Генерация музыки** - AI композиции (в разработке)

📝 **Поддерживаемые форматы:** MP3, WAV, M4A, OGG
🌍 **Языки:** Русский, английский, и многие другие

Выберите действие:"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_audio_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню аудио: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "news_menu")
async def show_news_menu(call: CallbackQuery, state: FSMContext):
    """
    📰 Новости и тренды - теперь часть бизнес-раздела
    """
    await state.clear()
    
    menu_text = """📰 **Новости и тренды**

🚀 **Мониторинг информационного поля:**

📱 **Мои каналы** - отслеживаемые источники информации
🔥 **Трендинг** - самые обсуждаемые темы для бизнеса
🎯 **Контент из новостей** - создание материалов на актуальные темы

## 💼 Бизнес-применение:
• Отслеживание отраслевых трендов
• Мониторинг конкурентов
• Поиск возможностей для контент-маркетинга
• Анализ рыночных изменений

Выберите действие:"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_news_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню новостей: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "my_projects_menu")
async def show_my_projects_menu(call: CallbackQuery, state: FSMContext):
    """
    🎭 Моя галерея - просмотр созданного AI-контента
    """
    await state.clear()
    
    menu_text = """🎭 **Моя галерея**

📚 **Весь ваш AI-контент в одном месте:**

🎭 **Мои аватары** - обученные персональные модели
🖼️ **Вся галерея** - все изображения и видео с умными фильтрами
⭐ **Избранное** - ваши лучшие работы
📊 **Статистика** - аналитика творческой активности

💾 **Весь контент автоматически сохраняется в высоком качестве**

Что хотите посмотреть?"""

    try:
        await base_handler.safe_edit_message(
            call,
            menu_text,
            reply_markup=get_my_projects_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка галереи: {e}")
        await call.answer("❌ Ошибка загрузки галереи", show_alert=True)

@router.callback_query(F.data == "gallery_all")
async def show_gallery_all(call: CallbackQuery, state: FSMContext):
    """
    🖼️ Вся галерея - показывает все созданные материалы
    """
    await state.clear()
    
    menu_text = """🖼️ **Вся галерея**

📚 **Здесь собрано всё ваше творчество:**
• Изображения с аватарами  
• Imagen4 генерации
• Hedra/Kling/Weo3 видео

🔍 **Используйте фильтры для поиска:**
• По типу контента
• По дате создания  
• Отмечайте лучшие как избранные

Выберите фильтр или действие:"""

    try:
        await base_handler.safe_edit_message(
            call,
            menu_text,
            reply_markup=get_gallery_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка галереи: {e}")
        await call.answer("❌ Ошибка загрузки галереи", show_alert=True)

# Обновленные плейсхолдер хэндлеры для новых callback_data
# avatar_create теперь обрабатывается в app.handlers.avatar.create

@router.callback_query(F.data == "imagen4_generation")  
async def start_imagen4_generation(call: CallbackQuery, state: FSMContext):
    """
    🎨 Imagen 4 Pro - генерация через Google Imagen4 (сразу запрос промпта)
    """
    # Сразу запрашиваем промпт без дополнительных меню
    from app.handlers.imagen4.imagen4_handler import imagen4_handler
    await imagen4_handler.show_prompt_input(call, state)

@router.callback_query(F.data == "hedra_video")
async def start_hedra_video(call: CallbackQuery, state: FSMContext):
    """
    🎭 Hedra AI - говорящие портреты
    """
    await call.answer("🎭 Hedra AI скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "kling_video")
async def start_kling_video(call: CallbackQuery, state: FSMContext):
    """
    🌟 Kling - кинематографическое видео
    """
    await call.answer("🌟 Kling скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "weo3_video")
async def start_weo3_video(call: CallbackQuery, state: FSMContext):
    """
    🎪 Weo3 - креативные видео эффекты
    """
    await call.answer("🎪 Weo3 скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "my_videos")
async def show_my_videos(call: CallbackQuery, state: FSMContext):
    """
    📹 Мои видео - архив созданных видео
    """
    await call.answer("📹 Архив видео скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "tts_menu")
async def show_tts_menu(call: CallbackQuery, state: FSMContext):
    """
    🗣️ TTS Озвучка - преобразование текста в речь
    """
    await call.answer("🗣️ TTS озвучка скоро будет доступна!", show_alert=True)

@router.callback_query(F.data == "music_generation")
async def start_music_generation(call: CallbackQuery, state: FSMContext):
    """
    🎵 Генерация музыки - создание AI музыки
    """
    await call.answer("🎵 Генерация музыки скоро будет доступна!", show_alert=True)

@router.callback_query(F.data == "my_channels")
async def show_my_channels(call: CallbackQuery, state: FSMContext):
    """
    📱 Мои каналы - управление подписками
    """
    await call.answer("📱 Управление каналами скоро будет доступно!", show_alert=True)

@router.callback_query(F.data == "add_to_chat")
async def show_add_to_chat_menu(call: CallbackQuery, state: FSMContext):
    """
    👥 Добавить бота в чат - управление рабочими чатами
    """
    await state.clear()
    
    menu_text = """👥 **Добавить бота в чат**

🤖 **Сделайте Aisha участником вашей команды:**

🔗 **Получить ссылку-приглашение** - добавьте бота в рабочую группу
📋 **Мои рабочие чаты** - управление подключенными чатами
⚙️ **Настройки парсинга** - что анализировать в переписке
📊 **Аналитика чатов** - статистика общения и настроений

💡 **Aisha автоматически анализирует переписку, выделяет задачи и отслеживает настроения команды**

Выберите действие:"""

    try:
        await base_handler.safe_edit_message(
            call,
            menu_text,
            reply_markup=get_add_to_chat_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню добавления в чат: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "add_channel")
async def add_channel(call: CallbackQuery, state: FSMContext):
    """
    ➕ Добавить канал - новая подписка
    """
    await call.answer("➕ Добавление каналов скоро будет доступно!", show_alert=True)

@router.callback_query(F.data == "content_from_news")
async def create_content_from_news(call: CallbackQuery, state: FSMContext):
    """
    🎯 Контент из новостей - создание на основе трендов
    """
    await call.answer("🎯 Создание контента из новостей скоро будет доступно!", show_alert=True)

# Галерея фильтры
@router.callback_query(F.data == "gallery_avatars")
async def show_gallery_avatars(call: CallbackQuery, state: FSMContext):
    """
    📸 Фото со мной - галерея изображений с лицом пользователя
    """
    await state.clear()
    
    # Импортируем обработчик фильтров галереи
    from app.handlers.gallery.filter_handler import gallery_filter_handler
    
    # Устанавливаем фильтр по типу "avatar" и показываем галерею
    await gallery_filter_handler.show_gallery_with_type_filter(call, state, "avatar")

@router.callback_query(F.data == "gallery_imagen")
async def show_gallery_imagen(call: CallbackQuery, state: FSMContext):
    """
    🖼️ Изображения - картинки созданные по описанию
    """
    await state.clear()
    
    # Импортируем обработчик фильтров галереи
    from app.handlers.gallery.filter_handler import gallery_filter_handler
    
    # Устанавливаем фильтр по типу "imagen4" и показываем галерею
    await gallery_filter_handler.show_gallery_with_type_filter(call, state, "imagen4")

@router.callback_query(F.data == "gallery_video")
async def show_gallery_video(call: CallbackQuery, state: FSMContext):
    """
    🎬 Только видео - фильтр галереи
    """
    await state.clear()
    
    # Импортируем обработчик фильтров галереи
    from app.handlers.gallery.filter_handler import gallery_filter_handler
    
    # Устанавливаем фильтр по типу "video" и показываем галерею
    await gallery_filter_handler.show_gallery_with_type_filter(call, state, "video")

@router.callback_query(F.data == "gallery_by_date")
async def show_gallery_by_date(call: CallbackQuery, state: FSMContext):
    """
    📅 По дате - сортировка галереи
    """
    await state.clear()
    
    # Импортируем обработчик фильтров галереи
    from app.handlers.gallery.filter_handler import gallery_filter_handler
    
    # Показываем меню фильтрации по дате
    await gallery_filter_handler.show_date_filter_menu(call, state)

@router.callback_query(F.data == "add_to_favorites")
async def add_to_favorites(call: CallbackQuery, state: FSMContext):
    """
    ⭐ Добавить в избранное - отметка контента
    """
    await call.answer("⭐ Добавление в избранное скоро будет доступно!", show_alert=True)

# Добавляю недостающие хэндлеры для аватарного подменю
@router.callback_query(F.data == "avatar_custom_prompt")
async def start_avatar_custom_prompt(call: CallbackQuery, state: FSMContext):
    """
    ✍️ Свой промпт - генерация аватара с пользовательским промптом
    """
    await call.answer("✍️ Генерация со своим промптом скоро будет доступна!", show_alert=True)

@router.callback_query(F.data == "avatar_from_photo")
async def start_avatar_from_photo(call: CallbackQuery, state: FSMContext):
    """
    📷 Генерация по фото - стилизация под референсное изображение
    """
    await call.answer("📷 Генерация по фото скоро будет доступна!", show_alert=True)

@router.callback_query(F.data == "avatar_styles")
async def show_avatar_styles(call: CallbackQuery, state: FSMContext):
    """
    🎨 Выбрать стиль - предустановленные стили для аватаров
    """
    await call.answer("🎨 Выбор стилей скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "favorites")
async def show_favorites(call: CallbackQuery, state: FSMContext):
    """
    ⭐ Избранное - коллекция отмеченных работ
    """
    await call.answer("⭐ Избранное скоро будет доступно!", show_alert=True)

@router.callback_query(F.data == "trending_today")
async def show_trending_today(call: CallbackQuery, state: FSMContext):
    """
    🔥 Трендинг сегодня - популярные посты за 24 часа
    """
    await call.answer("🔥 Трендинг сегодня скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "trending_week")
async def show_trending_week(call: CallbackQuery, state: FSMContext):
    """
    📊 Трендинг за неделю - долгосрочные тренды
    """
    await call.answer("📊 Трендинг за неделю скоро будет доступен!", show_alert=True)

@router.callback_query(F.data == "business_menu")
async def show_business_menu(call: CallbackQuery, state: FSMContext):
    """
    🤖 ИИ Ассистент - помощник для работы и повседневных задач
    """
    await state.clear()
    
    menu_text = """🤖 **ИИ Ассистент**

🎯 **Ваш умный помощник:**

🎯 **Задачи** - создавайте поручения с дедлайнами и следите за их выполнением
📰 **Новости** - отслеживайте важные новости и тренды по вашим темам
📝 **Голос в текст** - превращайте аудиосообщения в удобный текст
👥 **В группу** - добавьте бота в рабочий чат для анализа переписки

🚀 **Автоматизируйте рутину и экономьте время**

Выберите что нужно:"""

    try:
        await base_handler.safe_edit_message(
            call,
            menu_text,
            reply_markup=get_business_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню ИИ ассистента: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "tasks_menu")
async def show_tasks_menu(call: CallbackQuery, state: FSMContext):
    """
    📋 Задачи - система поручений для команды
    """
    await state.clear()
    
    menu_text = """📋 **Задачи**

🎯 **Управление поручениями:**

➕ **Создать** - дайте задание сотруднику с указанием срока
📊 **Мои поручения** - задачи которые вы выдали подчинённым
👥 **Команда** - все задачи команды и их статусы

⏰ **Напоминания** - автоматические уведомления о сроках
📈 **Отчеты** - статистика выполнения и эффективности

🤖 **Aisha будет напоминать о дедлайнах и собирать отчёты**

Что нужно сделать?"""

    try:
        await call.message.edit_text(
            menu_text,
            reply_markup=get_tasks_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.exception(f"Ошибка меню задач: {e}")
        await call.answer("❌ Ошибка загрузки меню", show_alert=True)

@router.callback_query(F.data == "create_task")
async def create_task(call: CallbackQuery, state: FSMContext):
    """
    ➕ Создать поручение - новая задача для сотрудника
    """
    await call.answer("➕ Создание поручений скоро будет доступно!", show_alert=True)

@router.callback_query(F.data == "my_tasks")
async def show_my_tasks(call: CallbackQuery, state: FSMContext):
    """
    📊 Мои поручения - выданные задачи
    """
    await call.answer("📊 Мои поручения скоро будут доступны!", show_alert=True)

@router.callback_query(F.data == "team_tasks")
async def show_team_tasks(call: CallbackQuery, state: FSMContext):
    """
    👥 Команда - задачи всей команды
    """
    await call.answer("👥 Командные задачи скоро будут доступны!", show_alert=True)

@router.callback_query(F.data == "task_reminders")
async def show_task_reminders(call: CallbackQuery, state: FSMContext):
    """
    ⏰ Напоминания - система уведомлений о дедлайнах
    """
    await call.answer("⏰ Напоминания скоро будут доступны!", show_alert=True)

@router.callback_query(F.data == "task_reports")
async def show_task_reports(call: CallbackQuery, state: FSMContext):
    """
    📈 Отчеты - аналитика выполнения задач
    """
    await call.answer("📈 Отчеты скоро будут доступны!", show_alert=True)

@router.callback_query(F.data == "get_invite_link")
async def get_invite_link(call: CallbackQuery, state: FSMContext):
    """
    🔗 Получить ссылку-приглашение для добавления в чат
    """
    await call.answer("🔗 Генерация ссылок скоро будет доступна!", show_alert=True)

@router.callback_query(F.data == "my_work_chats")
async def show_my_work_chats(call: CallbackQuery, state: FSMContext):
    """
    📋 Мои рабочие чаты - управление подключенными чатами
    """
    await call.answer("📋 Управление чатами скоро будет доступно!", show_alert=True)

@router.callback_query(F.data == "parsing_settings")
async def show_parsing_settings(call: CallbackQuery, state: FSMContext):
    """
    ⚙️ Настройки парсинга - что отслеживать в чатах
    """
    await call.answer("⚙️ Настройки парсинга скоро будут доступны!", show_alert=True)

@router.callback_query(F.data == "chat_analytics")
async def show_chat_analytics(call: CallbackQuery, state: FSMContext):
    """
    📊 Аналитика чатов - статистика активности
    """
    await call.answer("📊 Аналитика чатов скоро будет доступна!", show_alert=True) 