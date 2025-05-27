"""
Обработчики выбора типа обучения аватара
Критическая реализация из плана avatar_implementation_plan.md - Этап 0
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar_clean import (    get_training_type_keyboard,    get_training_type_confirmation_keyboard,    get_comparison_keyboard)
from app.texts.avatar import TRAINING_TYPE_TEXTS
from app.handlers.state import AvatarStates
from app.services.avatar.fal_training_service import FALTrainingService
from app.database.models import AvatarTrainingType
from app.core.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.callback_query(F.data == "select_training_type")
async def show_training_type_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор типа обучения аватара"""
    try:
        # Получаем информацию о режиме работы для отображения
        fal_service = FALTrainingService()
        config = fal_service.get_config_summary()
        
        # Базовый текст выбора типа
        text = TRAINING_TYPE_TEXTS["selection_menu"]
        
        # Добавляем информацию о режиме работы
        if config["test_mode"]:
            text += "\n\n🧪 **ТЕСТОВЫЙ РЕЖИМ** - обучение имитируется без реальных затрат"
        
        keyboard = get_training_type_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(AvatarStates.selecting_training_type)
        
        logger.info(f"Пользователь {callback.from_user.id} начал выбор типа обучения")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе выбора типа обучения: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data.startswith("training_type_"))
async def select_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа обучения"""
    try:
        training_type = callback.data.split("_", 2)[2]  # portrait, style, etc.
        
        # Валидируем тип обучения
        valid_types = [t.value for t in AvatarTrainingType]
        if training_type not in valid_types:
            await callback.answer(f"❌ Неизвестный тип обучения. Доступные: {', '.join(valid_types)}", show_alert=True)
            return
        
        # Сохраняем выбор в состоянии
        await state.update_data(training_type=training_type)
        
        # Получаем подробную информацию о выбранном типе
        fal_service = FALTrainingService()
        type_info = fal_service.get_training_type_info(training_type)
        
        # Показываем детальную информацию о выбранном типе
        text = TRAINING_TYPE_TEXTS[f"{training_type}_info"]
        keyboard = get_training_type_confirmation_keyboard(training_type)
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(AvatarStates.viewing_training_info)
        
        logger.info(f"Пользователь {callback.from_user.id} выбрал тип обучения: {training_type}")
        
    except Exception as e:
        logger.exception(f"Ошибка при выборе типа обучения: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data.startswith("confirm_training_"))
async def confirm_training_type(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора типа обучения и переход к выбору пола"""
    try:
        # Получаем training_type из callback_data или из состояния
        callback_training_type = callback.data.split("_", 2)[2]
        
        # ИСПРАВЛЕНИЕ: Если это "current", то это подтверждение готовности к обучению
        # из photo_upload, а не выбор типа обучения для нового аватара
        if callback_training_type == "current":
            # Перенаправляем к обработчику подтверждения обучения из photo_upload
            from .photo_upload import photo_handler
            await photo_handler.show_training_confirmation(callback, state)
            return
        
        # Для новых аватаров (portrait/style) - продолжаем обычную логику
        training_type = callback_training_type
        await state.update_data(training_type=training_type)
        
        # Получаем информацию о типе для подтверждения
        fal_service = FALTrainingService()
        type_info = fal_service.get_training_type_info(training_type)
        
        # Формируем текст подтверждения
        text = TRAINING_TYPE_TEXTS["training_type_saved"].format(
            type_name=type_info["name"]
        )
        
        await callback.message.edit_text(
            text=text,
            parse_mode="Markdown"
        )
        
        # Небольшая задержка перед переходом к выбору пола
        await asyncio.sleep(1)
        
        # Переход к выбору пола (только для новых аватаров)
        from .create import show_gender_selection
        await show_gender_selection(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} подтвердил тип обучения: {training_type}")
        
    except Exception as e:
        logger.exception(f"Ошибка при подтверждении типа обучения: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "compare_training_types")
async def show_training_types_comparison(callback: CallbackQuery, state: FSMContext):
    """Показывает сравнение типов обучения"""
    try:
        text = TRAINING_TYPE_TEXTS["detailed_comparison"]
        keyboard = get_comparison_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.set_state(AvatarStates.viewing_training_comparison)
        
        logger.info(f"Пользователь {callback.from_user.id} запросил сравнение типов обучения")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе сравнения типов: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "detailed_comparison")
async def show_detailed_comparison(callback: CallbackQuery, state: FSMContext):
    """Показывает подробное сравнение типов обучения"""
    try:
        # Это тот же обработчик, что и выше
        await show_training_types_comparison(callback, state)
        
    except Exception as e:
        logger.exception(f"Ошибка при показе подробного сравнения: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "back_to_avatar_menu")
async def back_to_avatar_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню аватаров"""
    try:
        # Очищаем состояние
        await state.clear()
        
        # Переходим к главному меню аватаров (используем новый handler)
        from .main import avatar_main_handler
        await avatar_main_handler.show_avatar_menu(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} вернулся к меню аватаров")
        
    except Exception as e:
        logger.exception(f"Ошибка при возврате к меню аватаров: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

# Добавляем импорт asyncio для задержки
import asyncio 