"""
Управление удалением изображений
Безопасное удаление с подтверждением
"""
import re
from uuid import UUID

from aiogram.types import CallbackQuery

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger
from ..cache import ultra_gallery_cache
from app.database.models import ImageGeneration

logger = get_logger(__name__)


class DeletionManager(BaseHandler):
    """Менеджер удаления изображений"""
    
    def _escape_markdown(self, text: str) -> str:
        """Экранирует специальные символы Markdown"""
        if not text:
            return text
        # Экранируем основные символы Markdown
        text = re.sub(r'([*_`\[\]()])', r'\\\1', text)
        return text
    
    async def request_delete_confirmation(self, callback: CallbackQuery):
        """Запрашивает подтверждение удаления изображения"""
        
        try:
            # Извлекаем generation_id из callback_data
            generation_id = callback.data.split(":")[1]
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получаем изображение для показа информации
            generation = await self._get_generation(UUID(generation_id), user.id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            logger.info(f"[Deletion Manager] Generation found: {generation.id}, user_id: {generation.user_id}")
            
            # Формируем сообщение с подтверждением
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # БЕЗОПАСНО обрабатываем промпт
            prompt_text = generation.final_prompt or generation.original_prompt or 'Без промпта'
            truncated_prompt = prompt_text[:100]
            if len(prompt_text) > 100:
                truncated_prompt += '...'
            
            # Экранируем Markdown-символы
            escaped_prompt = self._escape_markdown(truncated_prompt)
            
            text = f"""⚠️ **Подтверждение удаления**

🖼️ **Изображение:** {generation.id}

📝 **Промпт:** {escaped_prompt}

❓ **Вы уверены что хотите удалить это изображение?**

⚠️ _Это действие нельзя отменить!_"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="❌ Да, удалить", callback_data=f"gallery_delete_confirm:{generation_id}"),
                    InlineKeyboardButton(text="🔙 Отмена", callback_data="my_gallery")
                ]
            ])
            
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
                # Fallback: отправляем без форматирования
                logger.warning(f"Ошибка Markdown в подтверждении удаления, отправляю без форматирования: {msg_error}")
                
                plain_text = f"""⚠️ Подтверждение удаления

🖼️ Изображение: {generation.id}

📝 Промпт: {truncated_prompt}

❓ Вы уверены что хотите удалить это изображение?

⚠️ Это действие нельзя отменить!"""
                
                try:
                    if callback.message.photo:
                        await callback.message.delete()
                        await callback.message.answer(
                            text=plain_text,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        await callback.message.edit_text(
                            text=plain_text,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                except Exception:
                    # Последний fallback
                    await callback.answer("❌ Ошибка отображения", show_alert=True)
                    return
            
        except Exception as e:
            logger.exception(f"Ошибка запроса подтверждения удаления: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)
    
    async def _get_generation(self, generation_id: UUID, user_id: UUID):
        """Получает генерацию из БД"""
        
        from app.core.database import get_session
        from sqlalchemy import select
        
        async with get_session() as session:
            stmt = select(ImageGeneration).where(
                ImageGeneration.id == generation_id,
                ImageGeneration.user_id == user_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def delete_image(self, callback: CallbackQuery):
        """Удаление изображения с подтверждением"""
        
        try:
            # Извлекаем generation_id из callback_data
            generation_id = callback.data.split(":")[1]
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Удаляем изображение
            deleted = await self._delete_generation(UUID(generation_id), user.id)
            
            if deleted:
                # Очищаем кэш пользователя
                await ultra_gallery_cache.clear_all_cache(user.id)
                
                # Перенаправляем в галерею или показываем что галерея пуста
                await self._refresh_gallery_after_deletion(callback, user.id)
                
                await callback.answer("✅ Изображение удалено")
            else:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка удаления изображения: {e}")
            await callback.answer("❌ Ошибка удаления изображения", show_alert=True)
    
    async def _delete_generation(self, generation_id: UUID, user_id: UUID) -> bool:
        """Удаляет изображение из БД"""
        
        from app.core.database import get_session
        from sqlalchemy import select, delete
        
        async with get_session() as session:
            # Проверяем что изображение принадлежит пользователю
            stmt = select(ImageGeneration).where(
                ImageGeneration.id == generation_id,
                ImageGeneration.user_id == user_id
            )
            result = await session.execute(stmt)
            generation = result.scalar_one_or_none()
            
            if not generation:
                return False
            
            # Удаляем изображение
            delete_stmt = delete(ImageGeneration).where(
                ImageGeneration.id == generation_id,
                ImageGeneration.user_id == user_id
            )
            await session.execute(delete_stmt)
            await session.commit()
            
            logger.info(f"Image deleted: {generation_id} by user {user_id}")
            return True
    
    async def _refresh_gallery_after_deletion(self, callback: CallbackQuery, user_id: UUID):
        """Обновляет галерею после удаления изображения"""
        
        try:
            from ..viewer import GalleryViewer
            gallery_viewer = GalleryViewer()
            
            # Получаем обновленный список изображений
            images = await gallery_viewer.get_user_completed_images_ultra_fast(user_id)
            
            if not images:
                # Галерея пуста - показываем сообщение
                await gallery_viewer._show_empty_gallery_message(callback)
            else:
                # Показываем первое изображение (или последнее доступное)
                await gallery_viewer.send_image_card_ultra_fast(callback, images, 0, user_id)
            
        except Exception as e:
            logger.debug(f"Ошибка обновления галереи после удаления: {e}")
            # Fallback на главное меню
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]])
            
            await callback.message.edit_text(
                text="✅ Изображение удалено\n\n🔙 Возвращайтесь в главное меню",
                reply_markup=keyboard
            ) 