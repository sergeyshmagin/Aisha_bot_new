"""
Модуль навигации по галерее
Обработка переключения между изображениями
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from aiogram.types import CallbackQuery

from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from ..cache import ultra_gallery_cache, ImageCacheManager

logger = get_logger(__name__)


class NavigationHandler(BaseHandler):
    """Обработчик навигации по галерее"""
    
    def __init__(self):
        self.image_cache_manager = ImageCacheManager()
    
    async def handle_image_navigation(self, callback: CallbackQuery, direction: str):
        """⚡ БЫСТРАЯ навигация с сохранением фильтров"""
        
        try:
            # Извлекаем данные из callback_data
            data_parts = callback.data.split(":")
            current_idx = int(data_parts[1])
            
            # 🔥 УРОВЕНЬ 1: Быстрый поиск в сессионном кэше
            user_id = await self._get_user_id_from_session_cache(callback.from_user.id)
            
            # 🔥 УРОВЕНЬ 2: Если сессии нет - восстанавливаем через SQL (fallback)
            if not user_id:
                user_id = await self._restore_user_session(callback)
                if not user_id:
                    await callback.answer("🔄 Пожалуйста, перезайдите в галерею", show_alert=True)
                    return
            
            # 🎯 ПОЛУЧАЕМ ФИЛЬТРЫ ИЗ СОСТОЯНИЯ FSM
            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.base import StorageKey
            
            # Создаем ключ для получения состояния
            storage_key = StorageKey(
                bot_id=callback.bot.id,
                chat_id=callback.message.chat.id,
                user_id=callback.from_user.id
            )
            
            # Получаем состояние через FSMContext
            try:
                from app.core.di import get_state_storage
                storage = get_state_storage()
                state_data = await storage.get_data(storage_key)
                
                logger.debug(f"🔍 Данные состояния: {state_data}")
                
                # Извлекаем фильтры из состояния
                if state_data:
                    filters = {
                        'generation_type': state_data.get('generation_type'),
                        'start_date': state_data.get('start_date'),
                        'end_date': state_data.get('end_date')
                    }
                else:
                    # Если состояния нет, используем fallback
                    logger.warning("🔍 Состояние пустое - ищем в кэше текущие фильтры...")
                    filters = await self._get_filters_from_cache(user_id)
                
                logger.info(f"🔍 Навигация с фильтрами: {filters}")
                
            except Exception as state_error:
                logger.warning(f"Ошибка получения фильтров из состояния: {state_error}")
                # Fallback - пытаемся получить из кэша
                filters = await self._get_filters_from_cache(user_id)
                logger.info(f"🔍 Fallback фильтры из кэша: {filters}")
            
            # 🔥 УРОВЕНЬ 3: Получаем изображения с фильтрами
            images = await self._get_user_images_with_filters(user_id, callback, filters)
            if not images:
                return
            
            # Вычисляем новый индекс
            new_idx = self._calculate_new_index(current_idx, direction, len(images))
            
            # Если индекс не изменился, ничего не делаем
            if new_idx == current_idx:
                await callback.answer()
                return
            
            # 🚀 АГРЕССИВНО ПРЕДЗАГРУЖАЕМ следующие изображения (неблокирующе)
            asyncio.create_task(
                self.image_cache_manager.prefetch_adjacent_images(images, new_idx)
            )
            
            # ⚡ ПОКАЗЫВАЕМ новое изображение быстро С ФИЛЬТРАМИ
            from .main import GalleryViewer
            gallery_viewer = GalleryViewer()
            await gallery_viewer.send_image_card_ultra_fast(callback, images, new_idx, user_id, filters)
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"❌ Ошибка навигации: {e}")
            await callback.answer("❌ Ошибка навигации", show_alert=True)
    
    async def _get_user_id_from_session_cache(self, telegram_id: int) -> Optional[UUID]:
        """Быстрый поиск user_id в сессионном кэше Redis"""
        
        try:
            from app.core.di import get_redis
            redis = await get_redis()
            
            # Сканируем ключи сессий
            pattern = f"{ultra_gallery_cache._session_prefix}*"
            async for key in redis.scan_iter(match=pattern):
                try:
                    session_data_json = await redis.get(key)
                    if session_data_json:
                        import json
                        session_data = json.loads(session_data_json)
                        
                        if session_data.get('telegram_id') == telegram_id:
                            # Извлекаем user_id из ключа
                            user_id_str = key.decode().split(":")[-1]
                            return UUID(user_id_str)
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.exception(f"Ошибка поиска в кэше сессий: {e}")
            return None
    
    async def _restore_user_session(self, callback: CallbackQuery) -> Optional[UUID]:
        """Восстанавливает сессию пользователя через SQL"""
        
        telegram_id = callback.from_user.id
        logger.debug(f"Session cache miss, fallback to SQL for user {telegram_id}")
        
        user = await self.get_user_from_callback(callback, show_error=False)
        if not user:
            return None
        
        # Восстанавливаем сессию для следующих кликов
        await ultra_gallery_cache.set_session_data(user.id, {
            'telegram_id': telegram_id,
            'id': str(user.id),
            'username': user.username or '',
            'first_name': user.first_name
        })
        
        logger.debug(f"Session restored for user {user.id}")
        return user.id
    
    async def _get_user_images_with_fallback(self, user_id: UUID, callback: CallbackQuery):
        """Получает изображения пользователя с fallback на БД"""
        
        # Сначала пробуем кэш
        images = await ultra_gallery_cache.get_user_images(user_id)
        
        if not images:
            logger.debug(f"Images cache miss, loading from DB for user {user_id}")
            
            # Fallback на прямую загрузку из БД
            from .main import GalleryViewer
            gallery_viewer = GalleryViewer()
            # Передаем пустые фильтры для навигации
            filters = {'generation_type': None, 'start_date': None, 'end_date': None}
            images = await gallery_viewer.get_user_completed_images_ultra_fast(user_id, filters)
            
            if not images:
                await callback.answer("❌ Изображения не найдены", show_alert=True)
                return None
        
        return images
    
    async def _get_filters_from_cache(self, user_id: UUID) -> dict:
        """Получает фильтры из кэша галереи"""
        try:
            from app.core.di import get_redis
            redis = await get_redis()
            
            # Ищем активные фильтры в кэше галереи
            cache_key = f"gallery:active_filters:{user_id}"
            filters_json = await redis.get(cache_key)
            
            if filters_json:
                import json
                filters = json.loads(filters_json)
                logger.debug(f"🔍 Фильтры найдены в кэше: {filters}")
                return filters
            else:
                logger.debug(f"🔍 Фильтры в кэше не найдены")
                return {'generation_type': None, 'start_date': None, 'end_date': None}
                
        except Exception as e:
            logger.exception(f"Ошибка получения фильтров из кэша: {e}")
            return {'generation_type': None, 'start_date': None, 'end_date': None}

    async def _get_user_images_with_filters(self, user_id: UUID, callback: CallbackQuery, filters: dict) -> List:
        """Получает изображения пользователя с учетом фильтров"""
        try:
            from .main import GalleryViewer
            gallery_viewer = GalleryViewer()
            
            # Получаем изображения с фильтрами
            images = await gallery_viewer.get_user_completed_images_ultra_fast(user_id, filters)
            
            if not images:
                await callback.answer("📭 Изображения не найдены", show_alert=True)
                return []
            
            logger.debug(f"🖼️ Получено {len(images)} изображений с фильтрами: {filters}")
            return images
            
        except Exception as e:
            logger.exception(f"Ошибка получения изображений с фильтрами: {e}")
            await callback.answer("❌ Ошибка загрузки изображений", show_alert=True)
            return []
    
    @staticmethod
    def _calculate_new_index(current_idx: int, direction: str, total_images: int) -> int:
        """Вычисляет новый индекс для навигации"""
        
        if direction == "prev":
            return max(0, current_idx - 1)
        else:  # next
            return min(total_images - 1, current_idx + 1) 