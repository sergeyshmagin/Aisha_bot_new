"""
Главный обработчик галереи изображений
Улучшенная версия с карточным дизайном по образцу галереи аватаров
"""
import math
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

from app.core.di import get_user_service, get_avatar_service, get_redis
from app.core.database import get_session
from app.core.logger import get_logger
from app.services.generation.generation_service import ImageGenerationService
from app.database.models.generation import ImageGeneration, GenerationStatus
from app.database.models import Avatar
from app.shared.utils.telegram_utils import safe_edit_callback_message
from .states import GalleryStates
from app.database.repositories import ImageGenerationRepository
from app.services.user import UserService
from app.services.gallery_service import gallery_service
from app.handlers.gallery.states import GalleryData, gallery_state_manager
from app.utils.keyboards import create_gallery_keyboard

logger = get_logger(__name__)
router = Router()


class ImageGalleryCache:
    """Кэш для хранения состояния галереи пользователя с Redis поддержкой"""
    
    def __init__(self):
        self._memory_cache = {}  # Fallback кэш в памяти
    
    async def set_images(self, user_id: int, images: List[ImageGeneration], current_idx: int = 0):
        """Сохраняет изображения пользователя в кэш"""
        
        cache_data = {
            'image_ids': [str(img.id) for img in images],  # Сохраняем только ID
            'current_idx': current_idx,
            'total_count': len(images),
            'timestamp': datetime.now().isoformat()
        }
        
        # Пытаемся сохранить в Redis
        try:
            redis_client = await get_redis()
            cache_key = f"gallery_cache:{user_id}"
            
            # Сохраняем на 1 час
            await redis_client.setex(
                cache_key, 
                3600,  # 1 час TTL
                json.dumps(cache_data)
            )
            
            logger.debug(f"Кэш галереи для пользователя {user_id} сохранен в Redis")
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения в Redis, используем память: {e}")
        
        # Также сохраняем в памяти как fallback
        self._memory_cache[user_id] = {
            'images': images,
            'current_idx': current_idx,
            'total_count': len(images),
            'timestamp': datetime.now()
        }
    
    async def get_images(self, user_id: int) -> Optional[Dict]:
        """Получает изображения пользователя из кэша"""
        
        # Сначала пытаемся получить из Redis
        try:
            redis_client = await get_redis()
            cache_key = f"gallery_cache:{user_id}"
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                cache_info = json.loads(cached_data)
                
                # Восстанавливаем изображения по ID
                images = await self._restore_images_by_ids(cache_info['image_ids'])
                if images:
                    result = {
                        'images': images,
                        'current_idx': cache_info['current_idx'],
                        'total_count': len(images),
                        'timestamp': datetime.fromisoformat(cache_info['timestamp'])
                    }
                    
                    logger.debug(f"Кэш галереи для пользователя {user_id} получен из Redis")
                    return result
            
        except Exception as e:
            logger.warning(f"Ошибка получения из Redis, используем память: {e}")
        
        # Fallback на кэш в памяти
        return self._memory_cache.get(user_id)
    
    async def _restore_images_by_ids(self, image_ids: List[str]) -> List[ImageGeneration]:
        """Восстанавливает объекты изображений по их ID (ОПТИМИЗИРОВАННО - bulk запрос)"""
        
        try:
            if not image_ids:
                return []
            
            # 🚀 ОПТИМИЗАЦИЯ: Bulk запрос вместо N+1 запросов
            generation_service = ImageGenerationService()
            
            # Конвертируем в UUID
            uuid_ids = []
            for img_id in image_ids:
                try:
                    uuid_ids.append(UUID(img_id))
                except ValueError:
                    logger.warning(f"Невалидный UUID в кеше галереи: {img_id}")
                    continue
            
            if not uuid_ids:
                return []
            
            # Bulk запрос всех изображений сразу
            images = await generation_service.get_generations_by_ids(uuid_ids)
            
            # Фильтруем только завершенные с URL
            filtered_images = []
            for img in images:
                if img and img.status == GenerationStatus.COMPLETED and img.result_urls:
                    filtered_images.append(img)
            
            # Сортируем в том же порядке что и в image_ids
            sorted_images = []
            for img_id in image_ids:
                for img in filtered_images:
                    if str(img.id) == img_id:
                        sorted_images.append(img)
                        break
            
            logger.debug(f"Восстановлено {len(sorted_images)} изображений из {len(image_ids)} ID одним bulk запросом")
            return sorted_images
            
        except Exception as e:
            logger.exception(f"Ошибка восстановления изображений по ID: {e}")
            return []
    
    async def update_current_idx(self, user_id: int, new_idx: int):
        """Обновляет текущий индекс"""
        
        # Обновляем в Redis
        try:
            redis_client = await get_redis()
            cache_key = f"gallery_cache:{user_id}"
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                cache_info = json.loads(cached_data)
                cache_info['current_idx'] = new_idx
                
                await redis_client.setex(
                    cache_key, 
                    3600,  # Продлеваем TTL
                    json.dumps(cache_info)
                )
                
                logger.debug(f"Индекс галереи для пользователя {user_id} обновлен в Redis: {new_idx}")
            
        except Exception as e:
            logger.warning(f"Ошибка обновления индекса в Redis: {e}")
        
        # Обновляем в памяти
        if user_id in self._memory_cache:
            self._memory_cache[user_id]['current_idx'] = new_idx
    
    async def clear_user_cache(self, user_id: int):
        """Очищает кэш пользователя"""
        
        # Очищаем Redis
        try:
            redis_client = await get_redis()
            cache_key = f"gallery_cache:{user_id}"
            await redis_client.delete(cache_key)
            
            logger.debug(f"Кэш галереи для пользователя {user_id} очищен в Redis")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки Redis кэша: {e}")
        
        # Очищаем память
        if user_id in self._memory_cache:
            del self._memory_cache[user_id]


# Глобальный экземпляр кэша
gallery_cache = ImageGalleryCache()


class GalleryMainHandler:
    """Главный обработчик галереи изображений в карточном стиле"""
    
    def __init__(self):
        self.generation_service = ImageGenerationService()
    
    async def show_gallery_main(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главную страницу галереи"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            await callback.answer("🔄 Загружаю галерею...", show_alert=False)
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем изображения пользователя
            images = await self._get_user_completed_images(user.id)
            
            if not images:
                await self._show_empty_gallery_message(callback)
                return
            
            # Сохраняем в кэш
            await gallery_cache.set_images(user_telegram_id, images, 0)
            
            # Показываем первое изображение в карточном стиле
            await self._send_image_card(callback, images, 0)
            
            logger.info(f"Пользователь {user_telegram_id} открыл галерею ({len(images)} изображений)")
            
        except Exception as e:
            logger.exception(f"Ошибка показа галереи: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def handle_image_navigation(self, callback: CallbackQuery, direction: str):
        """Обрабатывает навигацию по изображениям"""
        try:
            user_telegram_id = callback.from_user.id
            current_idx = int(callback.data.split(":")[1])
            
            cache_data = await gallery_cache.get_images(user_telegram_id)
            if not cache_data:
                await callback.answer("❌ Данные галереи утеряны", show_alert=True)
                return
            
            images = cache_data["images"]
            total_images = len(images)
            
            # Циклическая навигация
            if direction == "prev":
                new_idx = (current_idx - 1) % total_images
            else:  # "next"
                new_idx = (current_idx + 1) % total_images
            
            # Обновляем кэш
            await gallery_cache.update_current_idx(user_telegram_id, new_idx)
            
            # Показываем новое изображение
            await self._send_image_card(callback, images, new_idx)
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка навигации по галерее: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _send_image_card(self, callback: CallbackQuery, images: List[ImageGeneration], img_idx: int):
        """Отправляет карточку изображения с превью"""
        
        if not images or img_idx >= len(images):
            await callback.message.edit_text("❌ Изображение не найдено")
            return
        
        generation = images[img_idx]
        
        # Формируем текст карточки
        text = self._format_image_card_text(generation, img_idx, len(images))
        
        # Создаем клавиатуру
        keyboard = self._get_image_card_keyboard(img_idx, len(images), str(generation.id))
        
        # Пытаемся загрузить и отправить изображение
        if generation.result_urls and len(generation.result_urls) > 0:
            try:
                image_data = await self._download_image(generation.result_urls[0])
                if image_data:
                    await self._send_card_with_image(callback, text, keyboard, image_data)
                    return
            except Exception as e:
                logger.warning(f"Не удалось загрузить изображение {generation.id}: {e}")
        
        # Если изображение не загрузилось, показываем только текст
        await self._send_card_text_only(callback, text, keyboard)
    
    def _format_image_card_text(self, generation: ImageGeneration, img_idx: int, total_images: int) -> str:
        """Форматирует текст карточки изображения"""
        
        # Безопасное название аватара (БЕЗ экранирования)
        avatar_name = generation.avatar.name if generation.avatar and generation.avatar.name else "Неизвестно"
        
        # Статус избранного
        favorite_status = "❤️ В избранном" if getattr(generation, 'is_favorite', False) else ""
        
        # Размер (безопасно)
        aspect_ratio = getattr(generation, 'aspect_ratio', '1:1')
        
        # Формируем упрощенную карточку БЕЗ промпта (есть кнопка "Промпт")
        text_parts = [
            f"🖼️ *Изображение {img_idx + 1} из {total_images}*",
            "",
            f"🎭 *Аватар:* {avatar_name}",
            f"📐 *Размер:* {aspect_ratio}"
        ]
        
        # Добавляем статус избранного если есть
        if favorite_status:
            text_parts.append("")
            text_parts.append(favorite_status)
        
        return "\n".join(text_parts)
    
    def _get_image_card_keyboard(self, img_idx: int, total_images: int, generation_id: str) -> InlineKeyboardMarkup:
        """Создает улучшенную клавиатуру для карточки изображения с лучшим UX"""
        
        buttons = []
        
        # 🔝 БЛОК 1: Фильтры и навигация по галерее (наверху)
        top_row = [
            InlineKeyboardButton(text="🔍 Фильтры", callback_data="gallery_filters"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="gallery_stats")
        ]
        buttons.append(top_row)
        
        # 🔄 БЛОК 2: Навигация по изображениям
        nav_row = []
        
        if img_idx > 0:
            nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"gallery_image_prev:{img_idx}"))
        else:
            nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="noop"))
        
        nav_row.append(InlineKeyboardButton(text=f"{img_idx + 1}/{total_images}", callback_data="noop"))
        
        if img_idx < total_images - 1:
            nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"gallery_image_next:{img_idx}"))
        else:
            nav_row.append(InlineKeyboardButton(text="➡️", callback_data="noop"))
        
        buttons.append(nav_row)
        
        # 📋 БЛОК 3: Действия с промптом и контентом
        content_row = [
            InlineKeyboardButton(text="📋 Промпт", callback_data=f"gallery_full_prompt:{generation_id}"),
            InlineKeyboardButton(text="🔄 Повторить", callback_data=f"gallery_regenerate:{generation_id}")
        ]
        buttons.append(content_row)
        
        # ❤️ БЛОК 4: Взаимодействие и управление
        interaction_row = [
            InlineKeyboardButton(text="❤️ Избранное", callback_data=f"gallery_toggle_favorite:{generation_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"gallery_delete:{generation_id}")
        ]
        buttons.append(interaction_row)
        
        # 🏠 БЛОК 5: Навигация по приложению
        back_row = [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
        buttons.append(back_row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def _send_card_with_image(self, callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup, image_data: bytes):
        """Отправляет карточку с изображением"""
        
        try:
            image_file = BufferedInputFile(image_data, filename="gallery_image.jpg")
            
            # Проверяем тип текущего сообщения
            if callback.message.photo:
                # Редактируем существующее фото
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=image_file, caption=text, parse_mode="Markdown"),
                    reply_markup=keyboard
                )
            else:
                # Удаляем текстовое сообщение и отправляем с фото
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                
                await callback.message.answer_photo(
                    photo=image_file,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        except TelegramBadRequest as markdown_error:
            if "parse entities" in str(markdown_error):
                # Проблема с Markdown - отправляем без форматирования
                logger.warning(f"Проблема с Markdown парсингом, отправляю без форматирования: {markdown_error}")
                try:
                    image_file = BufferedInputFile(image_data, filename="gallery_image.jpg")
                    
                    if callback.message.photo:
                        await callback.message.edit_media(
                            media=InputMediaPhoto(media=image_file, caption=text, parse_mode=None),
                            reply_markup=keyboard
                        )
                    else:
                        try:
                            await callback.message.delete()
                        except Exception:
                            pass
                        
                        await callback.message.answer_photo(
                            photo=image_file,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                except Exception as fallback_error:
                    logger.exception(f"Ошибка даже при fallback отправке изображения: {fallback_error}")
                    await self._send_card_text_only(callback, text, keyboard)
            else:
                logger.exception(f"Другая ошибка Telegram при отправке изображения: {markdown_error}")
                await self._send_card_text_only(callback, text, keyboard)
        except Exception as e:
            logger.exception(f"Общая ошибка отправки карточки с изображением: {e}")
            # Fallback на текстовую карточку
            await self._send_card_text_only(callback, text, keyboard)
    
    async def _send_card_text_only(self, callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup):
        """Отправляет карточку только с текстом"""
        
        error_suffix = "\n\n❌ *Изображение временно недоступно*"
        
        try:
            if callback.message.photo:
                # Удаляем фото и отправляем текст
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                
                await callback.message.answer(
                    text=text + error_suffix,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Редактируем текстовое сообщение
                await callback.message.edit_text(
                    text=text + error_suffix,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                
        except TelegramBadRequest as markdown_error:
            if "parse entities" in str(markdown_error):
                # Проблема с Markdown - отправляем без форматирования
                logger.warning(f"Проблема с Markdown парсингом в тексте, отправляю без форматирования: {markdown_error}")
                error_suffix_plain = "\n\n❌ Изображение временно недоступно"
                
                try:
                    if callback.message.photo:
                        try:
                            await callback.message.delete()
                        except Exception:
                            pass
                        
                        await callback.message.answer(
                            text=text + error_suffix_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        await callback.message.edit_text(
                            text=text + error_suffix_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                except Exception as fallback_error:
                    logger.exception(f"Критическая ошибка при fallback отправке текста: {fallback_error}")
                    await callback.answer("❌ Ошибка отображения карточки", show_alert=True)
            else:
                logger.exception(f"Другая ошибка Telegram при отправке текста: {markdown_error}")
                await callback.answer("❌ Ошибка отправки сообщения", show_alert=True)
        except Exception as e:
            logger.exception(f"Критическая ошибка отправки текстовой карточки: {e}")
            await callback.answer("❌ Критическая ошибка", show_alert=True)
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Скачивает изображение по URL"""
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.warning(f"HTTP {response.status} при скачивании изображения: {url}")
                        return None
                        
        except Exception as e:
            logger.exception(f"Ошибка скачивания изображения {url}: {e}")
            return None
    
    async def _get_user_completed_images(self, user_id: UUID) -> List[ImageGeneration]:
        """Получает завершенные изображения пользователя"""
        
        try:
            # Получаем все генерации
            all_images = await self.generation_service.get_user_generations(
                user_id=user_id,
                limit=1000,
                offset=0
            )
            
            # Фильтруем только завершенные и сортируем по дате (новые первые)
            completed_images = [
                img for img in all_images 
                if img.status == GenerationStatus.COMPLETED and img.result_urls
            ]
            
            # Сортируем по дате создания (новые первые)
            completed_images.sort(key=lambda x: x.created_at, reverse=True)
            
            return completed_images
            
        except Exception as e:
            logger.exception(f"Ошибка получения изображений пользователя: {e}")
            return []
    
    async def _show_empty_gallery_message(self, callback: CallbackQuery):
        """Показывает сообщение о пустой галерее"""
        
        text = """📷 **Ваша галерея пуста**

У вас пока нет сгенерированных изображений.

🎨 **Создайте первое изображение:**
• Выберите готовый шаблон
• Напишите свой промпт  
• Загрузите фото для анализа

✨ **После генерации** изображения появятся здесь!"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎨 Создать изображение", callback_data="generation_menu")
            ],
            [
                InlineKeyboardButton(text="🎭 Мои аватары", callback_data="avatar_menu")
            ],
            [
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]
        ])
        
        try:
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            # Если не удалось отредактировать
            await callback.message.answer(
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    
    async def show_gallery_stats(self, callback: CallbackQuery):
        """Показывает детальную статистику галереи с кешированием"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            # 🚀 ОПТИМИЗАЦИЯ: Проверяем кеш статистики
            try:
                redis_client = await get_redis()
                cache_key = f"gallery_stats:{user_telegram_id}"
                cached_stats = await redis_client.get(cache_key)
                
                if cached_stats:
                    import json
                    stats = json.loads(cached_stats)
                    logger.debug(f"Статистика получена из кеша для пользователя {user_telegram_id}")
                else:
                    stats = None
            except Exception as cache_error:
                logger.warning(f"Ошибка получения статистики из кеша: {cache_error}")
                stats = None
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Если кеша нет, вычисляем статистику
            if not stats:
                stats = await self._get_detailed_stats(user.id)
                
                # 🚀 Сохраняем в кеш на 5 минут
                try:
                    redis_client = await get_redis()
                    cache_key = f"gallery_stats:{user_telegram_id}"
                    import json
                    await redis_client.setex(cache_key, 300, json.dumps(stats))  # 5 минут TTL
                    logger.debug(f"Статистика сохранена в кеш для пользователя {user_telegram_id}")
                except Exception as cache_error:
                    logger.warning(f"Ошибка сохранения статистики в кеш: {cache_error}")
            
            text = f"""📊 *Детальная статистика галереи*

🖼️ *Изображения:* {stats['total_images']}

❤️ *Избранные:* {stats['favorite_images']}

🎭 *Аватары:*
• Используемых: {stats['used_avatars']}
• Активных: {stats['active_avatars']}

📅 *За 30 дней:*
• Создано: {stats['recent_images']} изображений
• Потрачено: \\~{stats['estimated_credits']} кредитов

🕐 *Последняя генерация:* {stats['last_generation']}

📈 *Наиболее активный период:* {stats['most_active_period']}"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery")
                ]
            ])
            
            # Безопасная отправка статистики
            try:
                if callback.message.photo:
                    # Если это сообщение с фото - удаляем и отправляем новое
                    try:
                        await callback.message.delete()
                    except Exception:
                        pass
                    
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
            except TelegramBadRequest as edit_error:
                if "parse entities" in str(edit_error):
                    # Проблема с Markdown - отправляем без форматирования
                    text_plain = text.replace('*', '').replace('\\~', '~')
                    
                    if callback.message.photo:
                        try:
                            await callback.message.delete()
                        except Exception:
                            pass
                        
                        await callback.message.answer(
                            text=text_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        await callback.message.edit_text(
                            text=text_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                else:
                    # Другая ошибка - отправляем новое сообщение
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа статистики: {e}")
            await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)
    
    async def _get_detailed_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Получает детальную статистику пользователя"""
        
        try:
            # Получаем все генерации
            all_generations = await self.generation_service.get_user_generations(
                user_id=user_id,
                limit=1000,
                offset=0
            )
            
            total_images = len(all_generations)
            
            # Избранные (пока заглушка)
            favorite_images = len([g for g in all_generations if getattr(g, 'is_favorite', False)])
            
            # Уникальные аватары
            used_avatars = len(set(g.avatar_id for g in all_generations if g.avatar_id))
            
            # Получаем активные аватары напрямую через сессию БД
            async with get_session() as session:
                from sqlalchemy import select
                from app.database.models import Avatar, AvatarStatus
                
                stmt = select(Avatar).where(
                    Avatar.user_id == user_id,
                    Avatar.status == AvatarStatus.COMPLETED
                )
                result = await session.execute(stmt)
                active_avatars = len(list(result.scalars().all()))
            
            # За 30 дней
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_images = len([g for g in all_generations if g.created_at >= thirty_days_ago])
            estimated_credits = recent_images * 5  # Примерная оценка
            
            # Последняя генерация
            last_generation = "Никогда"
            if all_generations:
                sorted_gens = sorted(all_generations, key=lambda x: x.created_at, reverse=True)
                last_generation = sorted_gens[0].created_at.strftime("%d.%m.%Y %H:%M")
            
            # Наиболее активный период (простая эвристика)
            most_active_period = "Утро (9:00-12:00)"  # Заглушка
            
            return {
                'total_images': total_images,
                'favorite_images': favorite_images,
                'used_avatars': used_avatars,
                'active_avatars': active_avatars,
                'recent_images': recent_images,
                'estimated_credits': estimated_credits,
                'last_generation': last_generation,
                'most_active_period': most_active_period
            }
            
        except Exception as e:
            logger.exception(f"Ошибка получения детальной статистики: {e}")
            return {
                'total_images': 0,
                'favorite_images': 0,
                'used_avatars': 0,
                'active_avatars': 0,
                'recent_images': 0,
                'estimated_credits': 0,
                'last_generation': "Ошибка загрузки",
                'most_active_period': "Неизвестно"
            }
    
    async def delete_image(self, callback: CallbackQuery, generation_id: str):
        """Показывает подтверждение удаления изображения"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию для проверки
            generation = await self.generation_service.get_generation_by_id(UUID(generation_id))
            if not generation:
                await callback.answer("❌ Изображение не найдено или не принадлежит вам", show_alert=True)
                return
            
            # Приводим оба ID к UUID для корректного сравнения
            try:
                generation_user_id = UUID(str(generation.user_id)) if not isinstance(generation.user_id, UUID) else generation.user_id
                user_id_uuid = UUID(str(user.id)) if not isinstance(user.id, UUID) else user.id
                
                if generation_user_id != user_id_uuid:
                    logger.warning(f"❌ Генерация {generation_id} не принадлежит пользователю {user_id_uuid} (владелец: {generation_user_id})")
                    await callback.answer("❌ Изображение не принадлежит вам", show_alert=True)
                    return
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Ошибка преобразования ID к UUID: {e}")
                await callback.answer("❌ Ошибка проверки прав доступа", show_alert=True)
                return
            
            # Формируем предварительный просмотр
            prompt_preview = generation.original_prompt[:40] + "..." if len(generation.original_prompt) > 40 else generation.original_prompt
            created_str = generation.created_at.strftime("%d.%m.%Y %H:%M")
            
            text = f"""🗑️ *Удаление изображения*

⚠️ *ВНИМАНИЕ!* Вы действительно хотите удалить это изображение?

📝 *Промпт:* {prompt_preview}
🎭 *Аватар:* {generation.avatar.name}
📅 *Создано:* {created_str}
🆔 *ID:* {str(generation.id)[:8]}

❗ *Это действие необратимо!*"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"gallery_delete_confirm:{generation_id}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="my_gallery")
                ],
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery")
                ]
            ])
            
            # Безопасная отправка
            try:
                if callback.message.photo:
                    try:
                        await callback.message.delete()
                    except Exception:
                        pass
                    
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            except Exception as send_error:
                logger.warning(f"Ошибка отправки подтверждения удаления: {send_error}")
                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=None
                )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа подтверждения удаления: {e}")
            await callback.answer("❌ Ошибка при удалении", show_alert=True)
    
    async def confirm_delete_image(self, callback: CallbackQuery, generation_id: str):
        """Подтверждает и выполняет удаление изображения"""
        
        user_telegram_id = callback.from_user.id
        
        try:
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(UUID(generation_id))
            if not generation:
                await callback.answer("❌ Изображение не найдено или не принадлежит вам", show_alert=True)
                return
            
            # Получаем текущий кэш галереи для определения позиции
            cache_data = await gallery_cache.get_images(user_telegram_id)
            current_idx = 0
            if cache_data:
                # Находим индекс удаляемого изображения
                for i, img in enumerate(cache_data["images"]):
                    if str(img.id) == generation_id:
                        current_idx = i
                        break
            
            # Выполняем удаление
            await self.generation_service.delete_generation(UUID(generation_id))
            
            # Обновляем список изображений после удаления
            updated_images = await self._get_user_completed_images(user.id)
            
            if not updated_images:
                # Если изображений больше нет, показываем пустую галерею
                await self._show_empty_gallery_message(callback)
                await callback.answer("🗑️ Изображение удалено. Галерея пуста", show_alert=True)
                return
            
            # Определяем новый индекс для показа
            new_idx = current_idx
            if new_idx >= len(updated_images):
                # Если удалили последнее изображение, показываем предпоследнее
                new_idx = len(updated_images) - 1
            
            # Обновляем кэш с новым списком и индексом
            await gallery_cache.set_images(user_telegram_id, updated_images, new_idx)
            
            # Показываем изображение на новой позиции
            await self._send_image_card(callback, updated_images, new_idx)
            
            await callback.answer("🗑️ Изображение удалено", show_alert=True)
            
            logger.info(f"Пользователь {user_telegram_id} удалил изображение {generation_id}, показано изображение на позиции {new_idx}")
            
        except Exception as e:
            logger.exception(f"Ошибка удаления изображения: {e}")
            await callback.answer("❌ Ошибка при удалении изображения", show_alert=True)


# Создаем экземпляр обработчика
gallery_main_handler = GalleryMainHandler()

# Регистрируем обработчики
@router.callback_query(F.data == "my_gallery")
async def handle_gallery_main(callback: CallbackQuery, state: FSMContext):
    """Обработчик главной страницы галереи"""
    await gallery_main_handler.show_gallery_main(callback, state)

@router.callback_query(F.data.startswith("gallery_image_prev:"))
async def handle_gallery_prev(callback: CallbackQuery):
    """Обработчик перехода к предыдущему изображению"""
    await gallery_main_handler.handle_image_navigation(callback, "prev")

@router.callback_query(F.data.startswith("gallery_image_next:"))
async def handle_gallery_next(callback: CallbackQuery):
    """Обработчик перехода к следующему изображению"""
    await gallery_main_handler.handle_image_navigation(callback, "next")

@router.callback_query(F.data == "gallery_stats")
async def handle_gallery_stats(callback: CallbackQuery):
    """Обработчик детальной статистики"""
    logger.info(f"📊 Обработка callback gallery_stats от пользователя {callback.from_user.id}")
    await gallery_main_handler.show_gallery_stats(callback)

@router.callback_query(F.data.startswith("gallery_full_prompt:"))
async def handle_gallery_full_prompt(callback: CallbackQuery):
    """Обработчик показа полного промпта"""
    try:
        logger.info(f"🔍 Обработка callback gallery_full_prompt: {callback.data} от пользователя {callback.from_user.id}")
        
        # Безопасное извлечение generation_id
        try:
            generation_id_str = callback.data.split(":")[1]
            generation_id = UUID(generation_id_str)
            logger.info(f"🆔 Извлечен generation_id: {generation_id}")
        except (IndexError, ValueError) as parse_error:
            logger.error(f"❌ Ошибка парсинга callback data '{callback.data}': {parse_error}")
            await callback.answer("❌ Неверный формат данных", show_alert=True)
            return
        
        # Получаем пользователя
        user_telegram_id = callback.from_user.id
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
            if not user:
                logger.warning(f"❌ Пользователь {user_telegram_id} не найден при показе промпта")
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
        
        logger.info(f"👤 Пользователь найден: {user.id}")
        
        # Получаем генерацию
        generation_service = ImageGenerationService()
        generation = await generation_service.get_generation_by_id(generation_id)
        
        if not generation:
            logger.warning(f"❌ Генерация {generation_id} не найдена в базе данных")
            await callback.answer("❌ Изображение не найдено", show_alert=True)
            return
            
        # Приводим оба ID к UUID для корректного сравнения
        try:
            generation_user_id = UUID(str(generation.user_id)) if not isinstance(generation.user_id, UUID) else generation.user_id
            user_id_uuid = UUID(str(user.id)) if not isinstance(user.id, UUID) else user.id
            
            if generation_user_id != user_id_uuid:
                logger.warning(f"❌ Генерация {generation_id} не принадлежит пользователю {user_id_uuid} (владелец: {generation_user_id})")
                await callback.answer("❌ Изображение не принадлежит вам", show_alert=True)
                return
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Ошибка преобразования ID к UUID: {e}")
            await callback.answer("❌ Ошибка проверки прав доступа", show_alert=True)
            return
        
        logger.info(f"🎨 Генерация найдена: {generation.id}, промпт длиной {len(generation.final_prompt)} символов")
        
        # Проверяем что промпт не пустой
        if not generation.final_prompt:
            logger.warning(f"❌ У генерации {generation_id} отсутствует final_prompt")
            await callback.answer("❌ Промпт недоступен", show_alert=True)
            return
        
        # Отправляем только блок кода с промптом
        prompt_text = f"""```
{generation.final_prompt}
```"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery"),
                InlineKeyboardButton(text="🎨 Генерация", callback_data="generation_menu")
            ]
        ])
        
        try:
            # Уровень 1: Попытка с Markdown
            await callback.message.reply(
                prompt_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Промпт отправлен с Markdown для генерации {generation_id}")
        except TelegramBadRequest as markdown_error:
            if "parse entities" in str(markdown_error):
                # Уровень 2: Проблема с Markdown - отправляем с HTML
                logger.warning(f"Проблема с Markdown в промпте, переключаюсь на HTML: {markdown_error}")
                
                # Переформатируем для HTML
                html_text = f"""<pre>{generation.final_prompt}</pre>"""
                
                try:
                    await callback.message.reply(
                        html_text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Промпт отправлен с HTML для генерации {generation_id}")
                except Exception as html_error:
                    # Уровень 3: Без форматирования
                    logger.exception(f"Ошибка и с HTML, отправляю без форматирования: {html_error}")
                    
                    await callback.message.reply(
                        generation.final_prompt,
                        reply_markup=keyboard,
                        parse_mode=None
                    )
                    logger.info(f"✅ Промпт отправлен без форматирования для генерации {generation_id}")
            else:
                # Другая ошибка Telegram
                logger.exception(f"Другая ошибка Telegram при показе промпта: {markdown_error}")
                await callback.answer("❌ Ошибка отображения промпта", show_alert=True)
                return
        
        await callback.answer("📝 Промпт отправлен!")
        logger.info(f"🎯 Успешно обработан callback gallery_full_prompt для генерации {generation_id}")
        
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка показа полного промпта: {e}")
        await callback.answer("❌ Ошибка показа промпта", show_alert=True)

# Заглушки для будущих функций
@router.callback_query(F.data.startswith("gallery_regenerate:"))
async def handle_gallery_regenerate(callback: CallbackQuery):
    """Обработчик повторной генерации"""
    await callback.answer("🚧 Повторная генерация в разработке", show_alert=True)

@router.callback_query(F.data.startswith("gallery_toggle_favorite:"))
async def handle_gallery_toggle_favorite(callback: CallbackQuery):
    """Обработчик избранного"""
    await callback.answer("🚧 Избранное в разработке", show_alert=True)

@router.callback_query(F.data.startswith("gallery_delete:"))
async def handle_gallery_delete(callback: CallbackQuery):
    """Обработчик удаления изображения"""
    generation_id = callback.data.split(":")[1]
    await gallery_main_handler.delete_image(callback, generation_id)

@router.callback_query(F.data.startswith("gallery_delete_confirm:"))
async def handle_gallery_delete_confirm(callback: CallbackQuery):
    """Обработчик подтверждения удаления изображения"""
    generation_id = callback.data.split(":")[1]
    await gallery_main_handler.confirm_delete_image(callback, generation_id)

@router.callback_query(F.data == "gallery_search")
async def handle_gallery_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик поиска в галерее - перенаправляет на фильтры"""
    
    # Перенаправляем на новую систему фильтров
    from .filter_handler import gallery_filter_handler
    await gallery_filter_handler.show_filter_menu(callback, state)

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработчик пустых callback'ов для неактивных кнопок"""
    await callback.answer()

async def show_gallery_image(callback_query: CallbackQuery, current_index: int, user_gallery_cache_key: str):
    """
    Показать изображение в галерее с оптимизацией
    """
    try:
        start_time = datetime.utcnow()
        user_id = UUID(str(callback_query.from_user.id))
        
        # ✅ 1. Получаем данные из кеша галереи
        gallery_data = await gallery_state_manager.get_gallery_data(user_gallery_cache_key)
        if not gallery_data:
            await callback_query.answer("❌ Данные галереи устарели. Обновляю...")
            await handle_gallery_main(callback_query)
            return
        
        # ✅ 2. Проверяем индекс
        if current_index < 0 or current_index >= len(gallery_data.image_ids):
            await callback_query.answer("❌ Изображение не найдено")
            return
        
        # ✅ 3. Получаем ID изображения
        image_id = UUID(gallery_data.image_ids[current_index])
        
        # ✅ 4. Получаем изображение через оптимизированный сервис
        image_data = await gallery_service.get_single_image_optimized(image_id, user_id)
        
        if not image_data:
            await callback_query.answer("❌ Изображение не найдено")
            return
        
        # ✅ 5. Обновляем текущий индекс в кеше
        await gallery_state_manager.update_gallery_index(user_gallery_cache_key, current_index)
        
        # ✅ 6. Формируем данные для отображения  
        text = _format_image_card_text(image_data, current_index + 1, gallery_data.total_count)
        keyboard = create_gallery_keyboard(current_index, gallery_data.total_count, str(image_id))
        
        # ✅ 7. Отправляем изображение
        image_url = image_data["result_urls"][0] if image_data.get("result_urls") else None
        
        if not image_url:
            await callback_query.answer("❌ Изображение недоступно")
            return
        
        # ✅ 8. Обработка разных типов сообщений
        try:
            if callback_query.message.photo:
                # Если текущее сообщение содержит фото, редактируем его
                await callback_query.message.edit_media(
                    media=InputMediaPhoto(media=image_url, caption=text),
                    reply_markup=keyboard
                )
            else:
                # Если текущее сообщение текстовое, удаляем и отправляем новое
                await callback_query.message.delete()
                await callback_query.message.answer_photo(
                    photo=image_url,
                    caption=text,
                    reply_markup=keyboard
                )
        except TelegramBadRequest as e:
            if "there is no text in the message to edit" in str(e).lower():
                # Fallback: удаляем и отправляем новое
                await callback_query.message.delete()
                await callback_query.message.answer_photo(
                    photo=image_url,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                logger.error(f"Ошибка отправки изображения: {e}")
                await callback_query.answer("❌ Ошибка загрузки изображения")
                return
        except Exception as e:
            logger.error(f"Критическая ошибка отправки изображения: {e}")
            await callback_query.answer("❌ Ошибка отображения")
            return
        
        # ✅ 9. Логируем производительность
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        logger.info(f"✅ Изображение {current_index + 1}/{gallery_data.total_count} показано за {duration:.0f}ms")
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа изображения в галерее: {e}")
        await callback_query.answer("❌ Произошла ошибка")


def _format_image_card_text(image_data: Dict, current: int, total: int) -> str:
    """Форматировать текст карточки изображения"""
    try:
        avatar_name = "Без аватара"
        if image_data.get("avatar"):
            avatar_name = image_data["avatar"].get("name", "Без имени")
        
        # Форматируем дату
        created_date = "Неизвестно"
        if image_data.get("created_at"):
            try:
                date_obj = datetime.fromisoformat(image_data["created_at"].replace('Z', '+00:00'))
                created_date = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                pass
        
        # Статус избранного
        favorite_status = "⭐" if image_data.get("is_favorite") else ""
        
        text = f"🖼️ *Изображение {current} из {total}* {favorite_status}\n\n"
        text += f"👤 *Аватар:* {avatar_name}\n"
        text += f"📐 *Размер:* {image_data.get('aspect_ratio', 'Неизвестно')}\n"
        text += f"🎨 *Качество:* {image_data.get('quality_preset', 'Стандарт')}\n"
        text += f"📅 *Создано:* {created_date}"
        
        return text
        
    except Exception as e:
        logger.error(f"Ошибка форматирования текста карточки: {e}")
        return f"🖼️ *Изображение {current} из {total}*"


async def _safe_send_message(callback_query: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup):
    """Безопасная отправка сообщения с fallback"""
    try:
        # Уровень 1: Попытка с разметкой
        if callback_query.message.photo:
            await callback_query.message.delete()
            await callback_query.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            
    except TelegramBadRequest as e:
        logger.warning(f"Ошибка парсинга Markdown: {e}")
        try:
            # Уровень 2: Fallback без разметки
            plain_text = text.replace("*", "").replace("_", "").replace("`", "")
            if callback_query.message.photo:
                await callback_query.message.delete()
                await callback_query.message.answer(plain_text, reply_markup=keyboard)
            else:
                await callback_query.message.edit_text(plain_text, reply_markup=keyboard)
                
        except Exception as fallback_error:
            logger.error(f"Критическая ошибка отправки сообщения: {fallback_error}")
            # Уровень 3: Минимальный fallback
            try:
                await callback_query.answer("❌ Ошибка отображения. Обновите галерею.")
            except:
                pass


@router.callback_query(F.data.startswith("gallery_next:"))
async def handle_gallery_next(callback_query: CallbackQuery):
    """Следующее изображение в галерее"""
    try:
        gallery_cache_key = callback_query.data.split(":", 1)[1]
        gallery_data = await gallery_state_manager.get_gallery_data(gallery_cache_key)
        
        if not gallery_data:
            await callback_query.answer("❌ Данные галереи устарели")
            await handle_gallery_main(callback_query)
            return
        
        next_index = gallery_data.current_index + 1
        if next_index >= len(gallery_data.image_ids):
            await callback_query.answer("❌ Это последнее изображение")
            return
        
        await show_gallery_image(callback_query, next_index, gallery_cache_key)
        
    except Exception as e:
        logger.error(f"Ошибка перехода к следующему изображению: {e}")
        await callback_query.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("gallery_prev:"))
async def handle_gallery_prev(callback_query: CallbackQuery):
    """Предыдущее изображение в галерее"""
    try:
        gallery_cache_key = callback_query.data.split(":", 1)[1]
        gallery_data = await gallery_state_manager.get_gallery_data(gallery_cache_key)
        
        if not gallery_data:
            await callback_query.answer("❌ Данные галереи устарели")
            await handle_gallery_main(callback_query)
            return
        
        prev_index = gallery_data.current_index - 1
        if prev_index < 0:
            await callback_query.answer("❌ Это первое изображение")
            return
        
        await show_gallery_image(callback_query, prev_index, gallery_cache_key)
        
    except Exception as e:
        logger.error(f"Ошибка перехода к предыдущему изображению: {e}")
        await callback_query.answer("❌ Произошла ошибка") 