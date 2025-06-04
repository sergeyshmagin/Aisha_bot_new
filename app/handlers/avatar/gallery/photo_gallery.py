"""
Обработчик фотогалереи аватаров
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from uuid import UUID
import logging

from aiogram.types import CallbackQuery, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.core.di import get_avatar_service
from app.core.logger import get_logger
from app.services.storage import StorageService
from .keyboards import GalleryKeyboards
from .models import gallery_cache

logger = get_logger(__name__)

class PhotoGalleryHandler:
    """Обработчик фотогалереи аватаров"""
    
    def __init__(self):
        self.keyboards = GalleryKeyboards()
    
    async def handle_view_avatar_photos(self, callback: CallbackQuery):
        """Показывает фотографии аватара"""
        try:
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем аватар с фотографиями
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                
                if not avatar or not avatar.photos:
                    await callback.answer("📸 У аватара нет фотографий", show_alert=True)
                    return
            
            # Сохраняем в кэш для навигации
            user_telegram_id = callback.from_user.id
            await gallery_cache.set_photos(user_telegram_id, avatar_id, avatar, 0)
            
            # Показываем первое фото
            await self.show_avatar_photo(callback, avatar, 0)
            
        except Exception as e:
            logger.exception(f"Ошибка при просмотре фотографий аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def show_avatar_photo(self, callback: CallbackQuery, avatar, photo_idx: int):
        """Показывает конкретное фото аватара"""
        try:
            if not avatar.photos or photo_idx >= len(avatar.photos):
                await callback.answer("📸 Фото не найдено", show_alert=True)
                return
            
            photo = avatar.photos[photo_idx]
            
            # Загружаем фото из MinIO
            storage = StorageService()
            
            # 🔧 ИСПРАВЛЕНИЕ: Убираем дублирование префикса "avatars/"
            # Если minio_key уже содержит "avatars/", используем его как есть
            # Если нет - добавляем префикс
            minio_key = photo.minio_key
            if minio_key.startswith("avatars/"):
                # Ключ уже содержит префикс - используем как object_name
                photo_data = await storage.download_file("avatars", minio_key)
            else:
                # Ключ без префикса - добавляем его
                photo_data = await storage.download_file("avatars", f"avatars/{minio_key}")
            
            logger.info(f"[Avatar Photo] Загружаем фото: bucket=avatars, key={minio_key}, размер={len(photo_data) if photo_data else 0} байт")
            
            if not photo_data:
                await callback.answer("❌ Не удалось загрузить фото", show_alert=True)
                return
            
            # Формируем информацию о фото
            text = self._format_photo_text(avatar, photo_idx, photo)
            
            keyboard = self.keyboards.get_avatar_photo_gallery_keyboard(
                photo_idx, 
                len(avatar.photos), 
                str(avatar.id)
            )
            
            # Отправляем фото
            photo_file = BufferedInputFile(photo_data, filename=f"photo_{photo_idx + 1}.jpg")
            await callback.message.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=text, parse_mode="Markdown"),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.exception(f"Ошибка при показе фото аватара: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке фото", show_alert=True)

    async def handle_photo_navigation(self, callback: CallbackQuery):
        """Навигация по фотографиям аватара (ОПТИМИЗИРОВАННАЯ - без SQL запросов при каждом клике)"""
        try:
            parts = callback.data.split(":")
            direction = parts[0].split("_")[-1]  # "prev" или "next"
            avatar_id = UUID(parts[1])
            current_idx = int(parts[2])
            
            user_telegram_id = callback.from_user.id
            cache_data = await gallery_cache.get_photos(user_telegram_id, avatar_id)
            
            if not cache_data:
                await callback.answer("❌ Данные фотогалереи утеряны", show_alert=True)
                return
            
            # 🚀 ОПТИМИЗАЦИЯ: Используем закешированный аватар вместо SQL запроса!
            avatar = cache_data.get("avatar")
            if not avatar or not avatar.photos:
                # Только если кеш поврежден, делаем запрос к БД
                logger.warning(f"Кеш аватара поврежден для {avatar_id}, запрашиваем из БД")
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.get_avatar(avatar_id)
                    
                if not avatar or not avatar.photos:
                    await callback.answer("❌ Фотографии не найдены", show_alert=True)
                    return
                    
                # Обновляем кеш
                await gallery_cache.set_photos(user_telegram_id, avatar_id, avatar, current_idx)
            
            if direction == "prev":
                new_idx = (current_idx - 1) % len(avatar.photos)
            else:  # "next"
                new_idx = (current_idx + 1) % len(avatar.photos)
            
            # Обновляем кеш с новым индексом
            await gallery_cache.update_photo_idx(user_telegram_id, avatar_id, new_idx)
            
            # 🚀 ДОПОЛНИТЕЛЬНАЯ ОПТИМИЗАЦИЯ: Продлеваем TTL при активной навигации
            await gallery_cache.extend_cache_ttl(user_telegram_id, avatar_id, ttl=600)
            
            # Показываем новое фото (БЕЗ дополнительных SQL запросов!)
            await self.show_avatar_photo(callback, avatar, new_idx)
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка при навигации по фотографиям: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_view_avatar_card(self, callback: CallbackQuery, state: FSMContext):
        """Возврат к карточке аватара из фотогалереи"""
        try:
            avatar_id = UUID(callback.data.split(":")[1])
            user_telegram_id = callback.from_user.id
            
            # Очищаем кэш фотогалереи
            await gallery_cache.clear_photos(user_telegram_id, avatar_id)
            
            # Получаем данные основной галереи
            cache_data = await gallery_cache.get_avatars(user_telegram_id)
            if not cache_data:
                # Если кэша нет, показываем галерею заново
                from .main_handler import GalleryHandler
                gallery_handler = GalleryHandler()
                await gallery_handler.show_avatar_gallery(callback, state)
                return
            
            avatars = cache_data["avatars"]
            
            # Находим индекс аватара - получаем актуальные аватары из БД
            from app.core.di import get_user_service, get_avatar_service
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                user_id = user.id
                
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars_with_photos(user_id)
            
            # Находим индекс аватара
            avatar_idx = 0
            for i, avatar in enumerate(avatars):
                if avatar.id == avatar_id:
                    avatar_idx = i
                    break
            
            # Обновляем кэш и показываем карточку
            await gallery_cache.update_current_idx(user_telegram_id, avatar_idx)
            
            # Используем AvatarCardsHandler для показа карточки
            from .avatar_cards import AvatarCardsHandler
            cards_handler = AvatarCardsHandler()
            await cards_handler.send_avatar_card(callback, user_id, avatars, avatar_idx)
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка при возврате к карточке аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    def _format_photo_text(self, avatar, photo_idx: int, photo) -> str:
        """Форматирует текст для фото"""
        return f"""🎭 **{avatar.name or 'Без имени'}**

📸 Фото {photo_idx + 1} из {len(avatar.photos)}

📅 Загружено: {photo.created_at.strftime("%d.%m.%Y %H:%M") if photo.created_at else "—"}""" 