"""
Управление повторной генерацией изображений
Воссоздание изображений с теми же параметрами
"""
from uuid import UUID

from aiogram.types import CallbackQuery

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger

logger = get_logger(__name__)


class RegenerationManager(BaseHandler):
    """Менеджер повторной генерации изображений"""
    
    async def regenerate_image(self, callback: CallbackQuery):
        """Повторная генерация изображения с теми же параметрами"""
        
        try:
            # Извлекаем generation_id из callback_data
            generation_id = callback.data.split(":")[1]
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получаем оригинальное изображение
            original_generation = await self._get_generation(UUID(generation_id), user.id)
            if not original_generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Показываем сообщение о начале генерации
            await callback.answer("🔄 Запущена повторная генерация...")
            
            # Запускаем генерацию
            await self._start_regeneration(callback, original_generation, user.id)
            
        except Exception as e:
            logger.exception(f"Ошибка повторной генерации: {e}")
            await callback.answer("❌ Ошибка запуска генерации", show_alert=True)
    
    async def _get_generation(self, generation_id: UUID, user_id: UUID):
        """Получает оригинальное изображение из БД"""
        
        from app.core.database import get_session
        from app.database.models.generation import ImageGeneration
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with get_session() as session:
            stmt = (
                select(ImageGeneration)
                .options(selectinload(ImageGeneration.avatar))
                .where(
                    ImageGeneration.id == generation_id,
                    ImageGeneration.user_id == user_id
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def _start_regeneration(self, callback: CallbackQuery, original_generation, user_id: UUID):
        """Запускает процесс повторной генерации"""
        
        try:
            # Подготавливаем параметры для новой генерации
            generation_params = {
                'prompt': original_generation.final_prompt or original_generation.original_prompt,
                'avatar_id': original_generation.avatar_id,
                'aspect_ratio': getattr(original_generation, 'aspect_ratio', '1:1'),
                'num_images': 1,  # Генерируем одно изображение
                'model': getattr(original_generation, 'model', 'flux-pro'),
                'lora_weights': getattr(original_generation, 'lora_weights', None)
            }
            
            # Ленивая инициализация generation_service
            from app.services.generation.generation_service import ImageGenerationService
            generation_service = ImageGenerationService()
            
            # Создаем новую задачу генерации
            new_generation = await generation_service.generate_custom(
                user_id=user_id,
                avatar_id=original_generation.avatar_id,
                custom_prompt=generation_params['prompt'],
                quality_preset=generation_params.get('aspect_ratio', 'balanced'),
                aspect_ratio=generation_params.get('aspect_ratio', '1:1'),
                num_images=generation_params.get('num_images', 1)
            )
            
            # Обновляем сообщение с информацией о новой генерации
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 Статус генерации", callback_data=f"generation_status:{new_generation.id}")
                ],
                [
                    InlineKeyboardButton(text="🖼️ Галерея", callback_data="gallery_main"),
                    InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
                ]
            ])
            
            text = f"""🔄 **Повторная генерация запущена**

📋 **Промпт:** {generation_params['prompt'][:100]}{'...' if len(generation_params['prompt']) > 100 else ''}

🎭 **Аватар:** {original_generation.avatar.name if original_generation.avatar else 'Без аватара'}

📐 **Размер:** {generation_params['aspect_ratio']}

⏱️ **Статус:** В обработке...

💡 _Генерация займет 1-3 минуты_"""
            
            # Правильная обработка сообщений с изображениями
            try:
                if callback.message.photo:
                    # Если это сообщение с фото - удаляем и отправляем новое
                    await callback.message.delete()
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    # Если это текстовое сообщение - редактируем
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            except Exception as msg_error:
                # Fallback: всегда удаляем и отправляем новое
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                    
                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            
            logger.info(f"Regeneration started: {new_generation.id} for user {user_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка запуска повторной генерации: {e}")
            
            # Fallback сообщение об ошибке
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Вернуться в галерею", callback_data="gallery_main")
            ]])
            
            await callback.message.edit_text(
                text="❌ **Ошибка повторной генерации**\n\n💡 _Попробуйте позже или создайте новое изображение_",
                reply_markup=keyboard,
                parse_mode="Markdown"
            ) 