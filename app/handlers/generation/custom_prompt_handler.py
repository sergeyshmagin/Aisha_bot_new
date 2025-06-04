"""
Обработчик кастомных промптов для генерации изображений
"""
from uuid import UUID

from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user, require_main_avatar
from app.core.logger import get_logger
from app.services.generation.generation_service import GENERATION_COST
from .states import GenerationStates
from .keyboards import build_custom_prompt_keyboard, build_aspect_ratio_keyboard
from app.shared.utils.telegram_utils import safe_edit_callback_message

logger = get_logger(__name__)


class CustomPromptHandler(BaseHandler):
    """Обработчик кастомных промптов"""
    
    @require_user()
    @require_main_avatar(check_completed=True)
    async def show_custom_prompt_input(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None,
        main_avatar=None
    ):
        """Показывает форму для ввода кастомного промпта"""
        
        try:
            # Извлекаем avatar_id из callback_data (gen_custom:{avatar_id})
            data_parts = callback.data.split(":")
            avatar_id = UUID(data_parts[1])
            
            # Проверяем что это тот же аватар
            if avatar_id != main_avatar.id:
                await callback.answer("❌ Неверный аватар", show_alert=True)
                return
            
            # Проверяем баланс
            if not await self.check_user_balance(
                user, 
                GENERATION_COST, 
                callback=callback
            ):
                return
            
            # Показываем форму для ввода промпта
            text = f"""📝 <b>Свой промпт</b>

🎭 <b>Аватар:</b> {main_avatar.name}
💰 <b>Стоимость:</b> {GENERATION_COST:.0f} единиц

✍️ <b>Напишите описание изображения:</b>

<i>Например: "красивая девушка в красном платье на фоне заката"</i>

⚠️ <b>Важно:</b>
• Описывайте на русском языке
• Будьте конкретны в деталях
• Избегайте неподходящего контента"""
            
            keyboard = build_custom_prompt_keyboard()
            
            # Сохраняем данные в состояние
            await state.update_data(
                avatar_id=str(avatar_id),
                user_id=str(user.id)
            )
            await state.set_state(GenerationStates.waiting_for_custom_prompt)
            
            # Используем безопасное редактирование
            success = await safe_edit_callback_message(
                callback=callback,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            if success:
                logger.info(f"Показана форма кастомного промпта для пользователя {user.telegram_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа формы кастомного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
            await self.safe_clear_state(state)
    
    async def process_custom_prompt(self, message: Message, state: FSMContext):
        """Обрабатывает введенный кастомный промпт"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = UUID(data.get("avatar_id"))
            user_id = UUID(data.get("user_id"))
            
            # Получаем пользователя
            user = await self.get_user_from_message(message)
            if not user or user.id != user_id:
                await message.reply("❌ Ошибка авторизации")
                await self.safe_clear_state(state)
                return
            
            # Получаем аватар
            avatar = await self.get_avatar_by_id(
                avatar_id, 
                user_id=user.id,
                message=message
            )
            if not avatar:
                await self.safe_clear_state(state)
                return
            
            # Проверяем статус аватара
            if avatar.status != "completed":
                await message.reply("❌ Аватар еще не готов к генерации!")
                await self.safe_clear_state(state)
                return
            
            # Проверяем баланс
            if not await self.check_user_balance(
                user, 
                GENERATION_COST, 
                message=message
            ):
                await self.safe_clear_state(state)
                return
            
            # Получаем текст промпта
            custom_prompt = message.text.strip()
            
            # Валидация промпта
            if len(custom_prompt) < 5:
                await message.reply("❌ Промпт слишком короткий. Минимум 5 символов.")
                return
            
            if len(custom_prompt) > 500:
                await message.reply("❌ Промпт слишком длинный. Максимум 500 символов.")
                return
            
            # Сохраняем промпт в состояние
            await state.update_data(
                custom_prompt=custom_prompt,
                avatar_name=avatar.name
            )
            
            # Показываем выбор соотношения сторон
            await self.show_aspect_ratio_selection(message, state)
            
        except Exception as e:
            logger.exception(f"Ошибка обработки кастомного промпта: {e}")
            await message.reply("❌ Произошла ошибка при обработке промпта")
            await self.safe_clear_state(state)
    
    async def show_aspect_ratio_selection(self, message: Message, state: FSMContext):
        """Показывает выбор соотношения сторон для кастомного промпта"""
        
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            custom_prompt = data.get("custom_prompt")
            avatar_name = data.get("avatar_name")
            
            text = f"""📐 <b>Выберите формат изображения</b>

🎭 <b>Аватар:</b> {avatar_name}
📝 <b>Промпт:</b> {custom_prompt[:100]}{"..." if len(custom_prompt) > 100 else ""}

👇 <b>Выберите соотношение сторон:</b>"""
            
            keyboard = build_aspect_ratio_keyboard()
            
            # Устанавливаем состояние ожидания выбора соотношения
            await state.set_state(GenerationStates.waiting_for_aspect_ratio_selection)
            
            await message.reply(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"Показан выбор соотношения сторон для кастомного промпта")
            
        except Exception as e:
            logger.exception(f"Ошибка показа выбора соотношения сторон: {e}")
            await message.reply("❌ Произошла ошибка")
            await self.safe_clear_state(state) 