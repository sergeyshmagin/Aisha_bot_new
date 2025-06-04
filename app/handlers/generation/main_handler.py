"""
Главный обработчик для системы генерации изображений
Рефакторен - использует новые модули для разделения ответственности
"""
from uuid import UUID

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user, require_main_avatar
from app.core.di import get_user_service
from app.core.logger import get_logger
from app.services.generation.generation_service import GENERATION_COST
from .states import GenerationStates
from .keyboards import build_generation_menu_keyboard
from .custom_prompt_handler import CustomPromptHandler
from .photo_prompt_handler import PhotoPromptHandler
from .generation_monitor import GenerationMonitor

logger = get_logger(__name__)
router = Router()


class GenerationMainHandler(BaseHandler):
    """Главный обработчик генерации изображений"""
    
    def __init__(self):
        self.custom_prompt_handler = CustomPromptHandler()
        self.photo_prompt_handler = PhotoPromptHandler()
        self.generation_monitor = GenerationMonitor()
    
    @require_user()
    @require_main_avatar(check_completed=True)
    async def show_generation_menu(
        self, 
        callback: CallbackQuery,
        user=None,
        main_avatar=None
    ):
        """Показывает главное меню генерации"""
        
        try:
            # Получаем баланс пользователя
            async with get_user_service() as user_service:
                user_balance = await user_service.get_user_balance(user.id)
            
            # Формируем текст
            avatar_type_text = "Портретный" if main_avatar.training_type.value == "portrait" else "Стилевой"
            
            text = f"""🎨 <b>Создание изображения</b>
👤 Основной аватар: {main_avatar.name} ({avatar_type_text})
💰 Баланс: {user_balance:.0f} единиц
💎 Стоимость: {GENERATION_COST:.0f} единиц за изображение

🔥 <b>Популярные стили</b>"""
            
            # Формируем клавиатуру
            keyboard = build_generation_menu_keyboard(
                popular_categories=[], 
                favorites=[], 
                avatar_id=main_avatar.id,
                user_balance=user_balance,
                generation_cost=GENERATION_COST
            )
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Показано меню генерации для пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню генерации: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def process_aspect_ratio_selection(self, callback: CallbackQuery, state: FSMContext):
        """Обрабатывает выбор соотношения сторон"""
        
        try:
            # Извлекаем данные из callback (aspect_ratio:width:height)
            data_parts = callback.data.split(":")
            if len(data_parts) != 3:
                await callback.answer("❌ Неверный формат данных", show_alert=True)
                return
            
            aspect_ratio = f"{data_parts[1]}:{data_parts[2]}"
            
            # Получаем данные из состояния
            data = await state.get_data()
            is_photo_analysis = data.get("is_photo_analysis", False)
            
            if is_photo_analysis:
                # Фото-анализ - передаем в photo_prompt_handler
                analysis_result = {
                    'prompt': data.get("custom_prompt"),
                    'analysis': data.get("original_analysis", "Анализ выполнен")
                }
                await self.photo_prompt_handler.start_photo_generation(
                    callback.message, state, aspect_ratio, analysis_result
                )
            else:
                # Кастомный промпт - передаем в generation_monitor
                await self.generation_monitor.start_generation_from_callback(
                    callback, state, aspect_ratio
                    )
            
        except Exception as e:
            logger.exception(f"Ошибка обработки выбора соотношения сторон: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
            await self.safe_clear_state(state)


# Создаем экземпляр обработчика
generation_handler = GenerationMainHandler()

# ==================== ОСНОВНЫЕ РОУТЫ ====================

@router.callback_query(F.data == "generation_menu")
async def handle_generation_menu(callback: CallbackQuery):
    """Обработчик главного меню генерации"""
    await generation_handler.show_generation_menu(callback)

@router.callback_query(F.data.startswith("gen_custom:"))
async def handle_custom_prompt_request(callback: CallbackQuery, state: FSMContext):
    """Обработчик запроса кастомного промпта"""
    await generation_handler.custom_prompt_handler.show_custom_prompt_input(callback, state)

@router.message(F.text, StateFilter(GenerationStates.waiting_for_custom_prompt))
async def handle_custom_prompt_text(message: Message, state: FSMContext):
    """Обработчик текста кастомного промпта"""
    await generation_handler.custom_prompt_handler.process_custom_prompt(message, state)

@router.callback_query(F.data.startswith("gen_photo:"))
async def handle_photo_prompt_request(callback: CallbackQuery, state: FSMContext):
    """Обработчик запроса фото-промпта"""
    await generation_handler.photo_prompt_handler.show_photo_prompt_input(callback, state)

@router.message(F.photo, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_reference_photo(message: Message, state: FSMContext):
    """Обработчик референсного фото от пользователя"""
    await generation_handler.photo_prompt_handler.process_reference_photo(message, state)

@router.message(F.document, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_reference_photo_document(message: Message, state: FSMContext):
    """Обработчик референсного фото как документа от пользователя"""
    await generation_handler.photo_prompt_handler.process_reference_photo(message, state)

@router.callback_query(F.data.startswith("aspect_ratio:"))
async def handle_aspect_ratio_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора соотношения сторон"""
    await generation_handler.process_aspect_ratio_selection(callback, state)

@router.callback_query(F.data.startswith("show_prompt:"))
async def handle_show_full_prompt(callback: CallbackQuery):
    """Обработчик показа полного промпта"""
    await generation_handler.generation_monitor.show_full_prompt(callback)

# ==================== ОБРАБОТЧИКИ ОШИБОК ====================

@router.message(F.text, StateFilter(GenerationStates.waiting_for_reference_photo))
async def handle_text_instead_of_photo(message: Message, state: FSMContext):
    """Обработчик текста вместо фото в состоянии ожидания фото"""
    await message.reply(
        "📸 Пожалуйста, отправьте изображение, а не текст.\n\n"
        "💡 Прикрепите фото к сообщению или отправьте изображение как файл.",
        parse_mode="HTML"
    )

@router.message(F.text, StateFilter(GenerationStates.waiting_for_aspect_ratio_selection))
async def handle_text_instead_of_aspect_ratio(message: Message, state: FSMContext):
    """Обработчик текста вместо выбора размера"""
    await message.reply(
        "📐 Пожалуйста, выберите размер изображения из предложенных вариантов.\n\n"
        "💡 Используйте кнопки выше для выбора соотношения сторон.",
        parse_mode="HTML"
    )

# ==================== ВСПОМОГАТЕЛЬНЫЕ РОУТЫ ====================

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработчик пустых callback'ов"""
    await callback.answer()

@router.callback_query(F.data == "gen_change_avatar")
async def handle_change_avatar_request(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает запрос на смену аватара"""
    # Импортируем обработчик аватаров
    from app.handlers.avatar import avatar_main_handler
    
    # Очищаем состояние, если есть
    await state.clear()
    
    # Перенаправляем на меню аватаров
    await avatar_main_handler.show_avatar_menu(callback, state)

# ==================== ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ ====================

@router.callback_query(F.data.startswith("gen_template:"))
async def handle_template_details(callback: CallbackQuery):
    """Обработчик деталей шаблона"""
    await callback.answer("🚧 Шаблоны стилей в разработке", show_alert=True)

@router.callback_query(F.data.startswith("gen_category:"))
async def show_category(callback: CallbackQuery):
    """Обработчик показа категории"""
    await callback.answer("🚧 Категории стилей в разработке", show_alert=True)

@router.callback_query(F.data == "gen_all_categories")
async def show_all_categories(callback: CallbackQuery):
    """Обработчик показа всех категорий"""
    await callback.answer("🚧 Каталог стилей в разработке", show_alert=True)

@router.callback_query(F.data == "gen_favorites")
async def show_favorites(callback: CallbackQuery):
    """Обработчик показа избранных"""
    await callback.answer("🚧 Избранные стили в разработке", show_alert=True)

@router.callback_query(F.data == "user_settings")
async def handle_user_settings_request(callback: CallbackQuery):
    """Обработчик запроса настроек пользователя"""
    await callback.answer("🚧 Настройки пользователя в разработке", show_alert=True)