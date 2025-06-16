"""
Управление избранными изображениями
Операции добавления/удаления из избранного
"""
from uuid import UUID

from aiogram.types import CallbackQuery

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger
from ..cache import ultra_gallery_cache
from app.database.models import ImageGeneration

logger = get_logger(__name__)


class FavoritesManager(BaseHandler):
    """Менеджер избранных изображений"""
    
    async def toggle_favorite(self, callback: CallbackQuery):
        """Переключение статуса избранного для изображения"""
        
        try:
            # Извлекаем generation_id из callback_data
            generation_id = callback.data.split(":")[1]
            
            # Получаем пользователя быстро
            user = await self.get_user_from_callback(callback, show_error=False)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Обновляем статус в БД
            await self._update_favorite_status(UUID(generation_id), user.id)
            
            # Очищаем кэш изображений пользователя (чтобы обновился статус)
            await ultra_gallery_cache.clear_all_cache(user.id)
            
            # Обновляем изображение
            await self._refresh_gallery_view(callback, user.id)
            
            await callback.answer("✅ Статус избранного обновлен")
            
        except Exception as e:
            logger.exception(f"Ошибка переключения избранного: {e}")
            await callback.answer("❌ Ошибка обновления избранного", show_alert=True)
    
    async def _update_favorite_status(self, generation_id: UUID, user_id: UUID):
        """Обновляет статус избранного в БД"""
        
        from app.core.database import get_session
        from sqlalchemy import select
        
        async with get_session() as session:
            # Получаем изображение
            stmt = select(ImageGeneration).where(
                ImageGeneration.id == generation_id,
                ImageGeneration.user_id == user_id
            )
            result = await session.execute(stmt)
            generation = result.scalar_one_or_none()
            
            if not generation:
                raise ValueError("Изображение не найдено")
            
            # Переключаем статус
            generation.is_favorite = not getattr(generation, 'is_favorite', False)
            
            await session.commit()
            
            logger.debug(f"Favorite status updated: {generation_id} -> {generation.is_favorite}")
    
    async def _refresh_gallery_view(self, callback: CallbackQuery, user_id: UUID):
        """Обновляет отображение галереи после изменения избранного"""
        
        try:
            # Получаем обновленные изображения
            from ..viewer import GalleryViewer
            gallery_viewer = GalleryViewer()
            
            # Получаем изображения без фильтров (общая галерея)
            images = await gallery_viewer.get_user_completed_images_ultra_fast(user_id, {})
            if not images:
                return
            
            # Находим текущий индекс из callback или используем 0
            current_idx = 0
            try:
                if callback.message and callback.message.reply_markup:
                    for row in callback.message.reply_markup.inline_keyboard:
                        for button in row:
                            if "/" in button.text and button.text.replace(" ", "").replace("/", "").isdigit():
                                parts = button.text.split("/")
                                if len(parts) == 2:
                                    current_idx = max(0, int(parts[0]) - 1)
                                    break
            except:
                current_idx = 0
            
            # Обновляем карточку с пустыми фильтрами
            await gallery_viewer.send_image_card_ultra_fast(callback, images, current_idx, user_id, {})
            
        except Exception as e:
            logger.debug(f"Ошибка обновления галереи после favorites: {e}")
            # Не падаем, просто логируем 