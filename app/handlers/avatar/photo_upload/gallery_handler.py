"""
Обработчик галереи фотографий
Выделен из app/handlers/avatar/photo_upload.py для соблюдения правила ≤500 строк

Переименован в PhotoUploadGalleryHandler для избежания конфликтов с другими галереями
"""
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from uuid import UUID
from typing import Dict, List, Optional
import logging
import json

from app.core.di import get_avatar_service, get_redis, get_user_service
from app.database.models import AvatarPhoto
from app.keyboards.photo_upload import get_photo_gallery_navigation_keyboard

logger = logging.getLogger(__name__)

class PhotoUploadGalleryHandler:
    """Обработчик галереи фотографий для загрузки (переименован из GalleryHandler)"""
    
    async def _get_gallery_cache(self, user_id: int) -> Optional[Dict]:
        """Получает кэш галереи из Redis"""
        try:
            redis_client = await get_redis()
            cache_key = f"photo_gallery_cache:{user_id}"
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
                
        except Exception as e:
            logger.warning(f"Ошибка получения кэша галереи из Redis: {e}")
            
        return None
    
    async def _set_gallery_cache(self, user_id: int, cache_data: Dict):
        """Сохраняет кэш галереи в Redis"""
        try:
            redis_client = await get_redis()
            cache_key = f"photo_gallery_cache:{user_id}"
            
            # Кэшируем на 10 минут
            await redis_client.setex(
                cache_key, 
                600,  # 10 минут TTL
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения кэша галереи в Redis: {e}")
    
    async def _clear_gallery_cache(self, user_id: int):
        """Очищает кэш галереи из Redis"""
        try:
            redis_client = await get_redis()
            cache_key = f"photo_gallery_cache:{user_id}"
            await redis_client.delete(cache_key)
            
        except Exception as e:
            logger.warning(f"Ошибка очистки кэша галереи из Redis: {e}")
    
    async def show_photo_gallery(self, callback: CallbackQuery, state: FSMContext):
        """Показывает галерею фотографий аватара"""
        try:
            user_id = callback.from_user.id
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id_str = data.get("avatar_id")
            
            if not avatar_id_str:
                await callback.answer("❌ Аватар не найден", show_alert=True)
                return
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем фотографии
            async with get_avatar_service() as avatar_service:
                photos, total = await avatar_service.get_avatar_photos(avatar_id)
            
            if not photos:
                await callback.answer("📸 Фотографии не найдены", show_alert=True)
                return
            
            # Кэшируем фотографии для навигации
            cache_data = {
                "photos": [{"id": str(p.id), "minio_key": p.minio_key, "width": p.width, "height": p.height, 
                           "created_at": p.created_at.isoformat()} for p in photos],
                "current_index": 0,
                "avatar_id": str(avatar_id)
            }
            await self._set_gallery_cache(user_id, cache_data)
            
            # Показываем первое фото
            await self._show_gallery_photo(callback, user_id, 0)
            
        except Exception as e:
            logger.exception(f"Ошибка при показе галереи: {e}")
            await callback.answer("❌ Ошибка при загрузке галереи", show_alert=True)

    async def _show_gallery_photo(self, callback: CallbackQuery, user_id: int, photo_index: int):
        """Показывает конкретное фото в галерее"""
        try:
            cache_data = await self._get_gallery_cache(user_id)
            if cache_data is None:
                await callback.answer("❌ Галерея не найдена", show_alert=True)
                return
            
            photos = cache_data["photos"]
            
            if photo_index < 0 or photo_index >= len(photos):
                await callback.answer("❌ Фото не найдено", show_alert=True)
                return
            
            photo = photos[photo_index]
            cache_data["current_index"] = photo_index
            
            # Обновляем кэш с новым индексом
            await self._set_gallery_cache(user_id, cache_data)
            
            # Получаем файл из MinIO
            from app.services.storage import StorageService
            storage = StorageService()
            
            try:
                file_data = await storage.download_file("avatars", photo["minio_key"])
                
                # Формируем caption с информацией о фото
                caption = f"""📸 Галерея фотографий

📊 Фото {photo_index + 1} из {len(photos)}
📅 Загружено: {photo['created_at'][:10]}
📏 Размер: {photo['width']}×{photo['height']} пикселей

💡 Используйте кнопки для навигации"""
                
                # Создаем клавиатуру навигации
                keyboard = get_photo_gallery_navigation_keyboard(
                    photo_index + 1, len(photos), photo["id"]
                )
                
                # Создаем BufferedInputFile для отправки
                from aiogram.types import BufferedInputFile
                photo_input = BufferedInputFile(file_data, filename=f"photo_{photo_index + 1}.jpg")
                
                # Отправляем или обновляем фото
                if callback.message.photo:
                    # Редактируем существующее фото
                    media = InputMediaPhoto(media=photo_input, caption=caption)
                    try:
                        await callback.message.edit_media(media=media, reply_markup=keyboard)
                    except Exception as edit_error:
                        # Fallback на удаление и пересоздание если редактирование не удалось
                        logger.warning(f"Не удалось отредактировать медиа, создаем новое: {edit_error}")
                        await callback.message.delete()
                        await callback.bot.send_photo(
                            chat_id=callback.message.chat.id,
                            photo=photo_input,
                            caption=caption,
                            reply_markup=keyboard
                        )
                else:
                    # Отправляем новое фото
                    await callback.bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=photo_input,
                        caption=caption,
                        reply_markup=keyboard
                    )
                
            except Exception as storage_error:
                logger.warning(f"Ошибка загрузки фото из MinIO: {storage_error}")
                await callback.answer("❌ Ошибка загрузки фото", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка при показе фото галереи: {e}")
            await callback.answer("❌ Ошибка при загрузке фото", show_alert=True)

    async def handle_gallery_navigation(self, callback: CallbackQuery, direction: str):
        """Обрабатывает навигацию по галерее"""
        try:
            user_id = callback.from_user.id
            
            cache_data = await self._get_gallery_cache(user_id)
            if cache_data is None:
                await callback.answer("❌ Галерея не найдена", show_alert=True)
                return
            
            current_index = cache_data["current_index"]
            photos_count = len(cache_data["photos"])
            
            if direction == "prev":
                new_index = max(0, current_index - 1)
            elif direction == "next":
                new_index = min(photos_count - 1, current_index + 1)
            else:
                await callback.answer("❌ Неизвестное направление", show_alert=True)
                return
            
            if new_index == current_index:
                await callback.answer()
                return
            
            await self._show_gallery_photo(callback, user_id, new_index)
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка навигации по галерее: {e}")
            await callback.answer("❌ Ошибка навигации", show_alert=True)

    async def handle_delete_photo(self, callback: CallbackQuery, avatar_id: UUID, photo_index: int):
        """Обрабатывает удаление фото из галереи"""
        try:
            user_id = callback.from_user.id
            
            cache_data = await self._get_gallery_cache(user_id)
            if cache_data is None:
                await callback.answer("❌ Галерея не найдена", show_alert=True)
                return
            
            photos = cache_data["photos"]
            
            if photo_index < 0 or photo_index >= len(photos):
                await callback.answer("❌ Фото не найдено", show_alert=True)
                return
            
            photo = photos[photo_index]
            
            # Получаем user UUID из БД
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                user_uuid = user.id
            
            # Удаляем фото через сервис с правильными параметрами
            async with get_avatar_service() as avatar_service:
                await avatar_service.delete_avatar_photo(UUID(photo["id"]), user_uuid)
            
            # Обновляем кэш
            photos.pop(photo_index)
            cache_data["photos"] = photos
            
            if not photos:
                # Если фото больше нет, закрываем галерею
                await callback.message.edit_text(
                    "📸 Все фотографии удалены.\n\nВернитесь к загрузке фотографий.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад к загрузке", callback_data="back_to_upload")]
                    ])
                )
                await self._clear_gallery_cache(user_id)
            else:
                # Показываем следующее фото или предыдущее
                new_index = min(photo_index, len(photos) - 1)
                cache_data["current_index"] = new_index
                await self._set_gallery_cache(user_id, cache_data)
                await self._show_gallery_photo(callback, user_id, new_index)
            
            await callback.answer("✅ Фото удалено")
            logger.info(f"Удалено фото {photo['id']} из аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении фото: {e}")
            await callback.answer("❌ Ошибка при удалении фото", show_alert=True)

    async def clear_gallery_cache(self, user_id: int):
        """Очищает кэш галереи для пользователя"""
        await self._clear_gallery_cache(user_id) 