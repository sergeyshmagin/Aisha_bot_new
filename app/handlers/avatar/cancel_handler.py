"""
Обработчики отмены создания аватара с улучшенным UX
Реализует рекомендации из docs/UX_CANCEL_GUIDELINES.md
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.keyboards.main import get_main_menu
from app.handlers.state import AvatarStates

logger = get_logger(__name__)
router = Router()


async def get_cancel_confirmation_dialog(step: str, context: dict = None) -> tuple[str, InlineKeyboardMarkup]:
    """
    Создаёт диалог подтверждения отмены в зависимости от этапа создания
    
    Args:
        step: Этап создания (training_type, gender, name, photos, training)
        context: Дополнительная информация (имя аватара, количество фото и т.д.)
        
    Returns:
        tuple[str, InlineKeyboardMarkup]: Текст и клавиатура диалога
    """
    
    if step == "training_type":
        # Начальный этап - минимальные потери
        text = """
⚠️ **Отмена создания аватара**

Вы действительно хотите вернуться в главное меню?

Выбранный тип обучения не будет сохранён.
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Да, отменить",
                    callback_data="confirm_cancel_creation_simple"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Продолжить создание",
                    callback_data="select_training_type"
                )
            ]
        ])
        
    elif step == "gender":
        # Черновик уже создан
        text = """
⚠️ **Отмена создания аватара**

Вы действительно хотите отменить создание?

🗑️ **Будет удалено:**
• Черновик аватара
• Выбранный тип обучения

💡 **Альтернатива:** Вернуться к предыдущему шагу
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Да, удалить всё",
                    callback_data="confirm_cancel_with_cleanup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К выбору типа",
                    callback_data="select_training_type"
                ),
                InlineKeyboardButton(
                    text="◀️ Продолжить",
                    callback_data="cancel_cancel"
                )
            ]
        ])
        
    elif step == "photos":
        # Критический этап - загружены фотографии
        avatar_name = context.get("avatar_name", "Без имени") if context else "Без имени"
        photos_count = context.get("photos_count", 0) if context else 0
        
        text = f"""
⚠️ **ВНИМАНИЕ: Отмена создания аватара**

Вы уверены что хотите отменить создание?

🗑️ **Будет БЕЗВОЗВРАТНО удалено:**
• Аватар "{avatar_name}"
• {photos_count} загруженных фотографий
• Весь прогресс создания

⚠️ **Это действие нельзя отменить!**

💡 **Рекомендация:** Сохранить как черновик и вернуться позже
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить черновик",
                    callback_data="save_as_draft"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Да, удалить всё",
                    callback_data="confirm_cancel_with_cleanup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Продолжить создание",
                    callback_data="cancel_cancel"
                )
            ]
        ])
        
    elif step == "training":
        # Максимальная критичность - процесс обучения
        avatar_name = context.get("avatar_name", "Аватар") if context else "Аватар"
        progress = context.get("progress", 0) if context else 0
        time_spent = context.get("time_spent", "неизвестно") if context else "неизвестно"
        
        text = f"""
⚠️ **КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ**

**Отмена обучения аватара "{avatar_name}"**

⏱️ **Текущий прогресс:** {progress}% завершено
🕐 **Затрачено времени:** {time_spent}
💸 **Потраченные ресурсы** будут потеряны

⚠️ **ВНИМАНИЕ:**
• Отменённое обучение НЕЛЬЗЯ восстановить
• Придётся начинать заново
• Время и ресурсы не вернуть

🤔 **Вы ДЕЙСТВИТЕЛЬНО уверены?**
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Да, я полностью уверен",
                    callback_data="confirm_cancel_training_final"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏸️ Приостановить",
                    callback_data="pause_training"
                ),
                InlineKeyboardButton(
                    text="◀️ Продолжить",
                    callback_data="cancel_cancel_training"
                )
            ]
        ])
        
    else:
        # Универсальный диалог
        text = """
⚠️ **Отмена действия**

Вы действительно хотите отменить текущее действие?
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Да, отменить",
                    callback_data="confirm_cancel_simple"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Продолжить",
                    callback_data="cancel_cancel"
                )
            ]
        ])
    
    return text, keyboard


@router.callback_query(F.data == "cancel_avatar_creation")
async def handle_cancel_creation_request(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает запрос на отмену создания аватара"""
    try:
        # Определяем текущий этап
        current_state = await state.get_state()
        data = await state.get_data()
        
        if current_state == AvatarStates.selecting_training_type:
            step = "training_type"
            context = None
        elif current_state == AvatarStates.selecting_gender:
            step = "gender"
            context = data
        elif current_state == AvatarStates.uploading_photos:
            step = "photos"
            context = {
                "avatar_name": data.get("avatar_name", "Без имени"),
                "photos_count": data.get("photos_count", 0)
            }
        elif current_state == AvatarStates.training:
            step = "training"
            context = {
                "avatar_name": data.get("avatar_name", "Аватар"),
                "progress": data.get("training_progress", 0),
                "time_spent": data.get("time_spent", "неизвестно")
            }
        else:
            step = "general"
            context = None
        
        # Показываем соответствующий диалог
        text, keyboard = await get_cancel_confirmation_dialog(step, context)
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} запросил отмену на этапе: {step}")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе диалога отмены: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "confirm_cancel_creation_simple")
async def handle_simple_cancel(callback: CallbackQuery, state: FSMContext):
    """Простая отмена без очистки данных"""
    try:
        await state.clear()
        
        # Возвращаем в главное меню
        keyboard = get_main_menu()
        
        await callback.message.edit_text(
            text="✅ **Создание аватара отменено**\n\nВы можете начать создание нового аватара в любое время.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} отменил создание (простая отмена)")
        
    except Exception as e:
        logger.exception(f"Ошибка при простой отмене: {e}")
        await callback.answer("❌ Ошибка отмены", show_alert=True)


@router.callback_query(F.data == "confirm_cancel_with_cleanup")
async def handle_cancel_with_cleanup(callback: CallbackQuery, state: FSMContext):
    """Отмена с полной очисткой данных и удалением черновика"""
    try:
        data = await state.get_data()
        avatar_id = data.get("avatar_id")
        avatar_name = data.get("avatar_name", "аватара")
        
        # Если есть созданный аватар, удаляем его
        if avatar_id:
            user_telegram_id = callback.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                
                if user:
                    async with get_avatar_service() as avatar_service:
                        success = await avatar_service.delete_avatar_completely(avatar_id)
                        if success:
                            logger.info(f"Аватар {avatar_id} удален при отмене пользователем {user_telegram_id}")
        
        # Очищаем состояние
        await state.clear()
        
        # Показываем подтверждение
        text = f"""
🗑️ **Создание отменено**

Черновик "{avatar_name}" и все данные удалены.

Вы можете начать создание нового аватара в любое время.
"""
        
        keyboard = get_main_menu()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} отменил создание с очисткой")
        
    except Exception as e:
        logger.exception(f"Ошибка при отмене с очисткой: {e}")
        await callback.answer("❌ Ошибка отмены", show_alert=True)


@router.callback_query(F.data == "save_as_draft")
async def handle_save_as_draft(callback: CallbackQuery, state: FSMContext):
    """Сохраняет прогресс как черновик"""
    try:
        data = await state.get_data()
        avatar_name = data.get("avatar_name", "Черновик")
        
        # В данной реализации черновики уже сохраняются автоматически
        # Просто очищаем состояние, оставляя аватар в БД
        await state.clear()
        
        text = f"""
💾 **Прогресс сохранён**

Аватар "{avatar_name}" сохранён как черновик.

Вы можете вернуться к его созданию через меню "Мои аватары".
"""
        
        keyboard = get_main_menu()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} сохранил аватар как черновик")
        
    except Exception as e:
        logger.exception(f"Ошибка при сохранении черновика: {e}")
        await callback.answer("❌ Ошибка сохранения", show_alert=True)


@router.callback_query(F.data == "cancel_cancel")
async def handle_cancel_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена отмены - возврат к предыдущему экрану"""
    try:
        current_state = await state.get_state()
        
        if current_state == AvatarStates.selecting_training_type:
            from app.handlers.avatar.training_type_selection import show_training_type_selection
            await show_training_type_selection(callback, state)
        elif current_state == AvatarStates.selecting_gender:
            from app.handlers.avatar.create import show_gender_selection
            await show_gender_selection(callback, state)
        elif current_state == AvatarStates.uploading_photos:
            from app.handlers.avatar.photo_upload import continue_photo_upload
            await continue_photo_upload(callback, state)
        else:
            # Возврат в главное меню аватаров по умолчанию
            from app.handlers.avatar.main import avatar_main_handler
            await avatar_main_handler.show_avatar_menu(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} отменил отмену")
        
    except Exception as e:
        logger.exception(f"Ошибка при отмене отмены: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True) 