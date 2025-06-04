"""
Модуль для просмотра галереи изображений
"""
import aiohttp
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.core.logger import get_logger
from app.database.models.generation import ImageGeneration, GenerationStatus
from app.services.generation.generation_service import ImageGenerationService
from .keyboards import build_gallery_image_keyboard, build_empty_gallery_keyboard

logger = get_logger(__name__)


class ImageGalleryCache:
    """Кэш для ускорения навигации по галерее (из старого кода)"""
    
    def __init__(self):
        self._cache = {}
    
    async def get_user_images(self, user_id: UUID) -> Optional[List[ImageGeneration]]:
        """Получает изображения из кэша"""
        cache_key = f"user_{user_id}"
        cached_data = self._cache.get(cache_key)
        
        if cached_data:
            # Проверяем возраст кэша (5 минут)
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=5):
                logger.debug(f"Изображения получены из кэша для пользователя {user_id}")
                return cached_data['images']
        
        return None
    
    async def set_user_images(self, user_id: UUID, images: List[ImageGeneration]):
        """Сохраняет изображения в кэш"""
        cache_key = f"user_{user_id}"
        
        self._cache[cache_key] = {
            'images': images,
            'timestamp': datetime.now()
        }
        logger.debug(f"Изображения сохранены в кэш для пользователя {user_id}: {len(images)} штук")
    
    async def clear_user_cache(self, user_id: UUID):
        """Очищает кэш пользователя"""
        cache_key = f"user_{user_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    async def set_user_gallery_state(self, user_id: UUID, current_index: int):
        """Сохраняет текущий индекс галереи в Redis"""
        try:
            from app.core.di import get_redis
            from datetime import datetime
            
            redis_client = await get_redis()
            
            state_key = f"gallery_state:{user_id}"
            state_data = {
                'current_index': current_index,
                'timestamp': datetime.now().isoformat()
            }
            
            import json
            await redis_client.setex(
                state_key,
                1800,  # 30 минут TTL
                json.dumps(state_data)
            )
            
            logger.debug(f"Состояние галереи сохранено в Redis: пользователь {user_id}, индекс {current_index}")
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения состояния галереи в Redis: {e}")
    
    async def get_user_gallery_state(self, user_id: UUID) -> Optional[int]:
        """Получает текущий индекс галереи из Redis"""
        try:
            from app.core.di import get_redis
            redis_client = await get_redis()
            
            state_key = f"gallery_state:{user_id}"
            cached_state = await redis_client.get(state_key)
            
            if cached_state:
                import json
                state_data = json.loads(cached_state)
                current_index = state_data.get('current_index', 0)
                
                logger.debug(f"Состояние галереи получено из Redis: пользователь {user_id}, индекс {current_index}")
                return current_index
            
        except Exception as e:
            logger.warning(f"Ошибка получения состояния галереи из Redis: {e}")
        
        return None
    
    async def clear_user_gallery_state(self, user_id: UUID):
        """Очищает состояние галереи из Redis"""
        try:
            from app.core.di import get_redis
            redis_client = await get_redis()
            
            state_key = f"gallery_state:{user_id}"
            await redis_client.delete(state_key)
            
            logger.debug(f"Состояние галереи очищено из Redis для пользователя {user_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки состояния галереи из Redis: {e}")


# Глобальный экземпляр кэша
gallery_cache = ImageGalleryCache()


class GalleryViewer(BaseHandler):
    """Класс для просмотра галереи изображений"""
    
    def __init__(self):
        self.generation_service = ImageGenerationService()
    
    @require_user()
    async def show_gallery_main(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None,
        start_index: Optional[int] = None
    ):
        """Показывает главную страницу галереи"""
        
        try:
            # Очищаем состояние если есть
            await self.safe_clear_state(state)
            
            # Получаем изображения пользователя
            images = await self._get_user_completed_images(user.id)
            
            if not images:
                await self._show_empty_gallery_message(callback)
                return
            
            # Определяем стартовый индекс
            if start_index is not None:
                # Используем переданный индекс
                img_idx = max(0, min(start_index, len(images) - 1))
                logger.info(f"Используем переданный стартовый индекс: {img_idx}")
            else:
                # Пытаемся восстановить состояние из Redis
                saved_index = await gallery_cache.get_user_gallery_state(user.id)
                if saved_index is not None and saved_index < len(images):
                    img_idx = saved_index
                    logger.info(f"Восстановлен индекс из Redis: {img_idx}")
                else:
                    img_idx = 0
                    logger.info(f"Используем начальный индекс: {img_idx}")
            
            # Показываем изображение
            await self._send_image_card(callback, images, img_idx)
            
            logger.info(f"Показана галерея для пользователя {user.telegram_id}: {len(images)} изображений, индекс {img_idx}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа галереи: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)
    
    async def handle_image_navigation(self, callback: CallbackQuery, direction: str):
        """Обрабатывает навигацию по изображениям"""
        
        try:
            # Извлекаем индекс из callback_data
            data_parts = callback.data.split(":")
            current_idx = int(data_parts[1])
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                return
            
            # Получаем изображения
            images = await self._get_user_completed_images(user.id)
            if not images:
                await callback.answer("❌ Изображения не найдены", show_alert=True)
                return
            
            # Вычисляем новый индекс
            if direction == "prev":
                new_idx = max(0, current_idx - 1)
            else:  # next
                new_idx = min(len(images) - 1, current_idx + 1)
            
            # Если индекс не изменился, ничего не делаем
            if new_idx == current_idx:
                await callback.answer()
                return
            
            # Показываем новое изображение
            await self._send_image_card(callback, images, new_idx)
            
        except Exception as e:
            logger.exception(f"Ошибка навигации по галерее: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _send_image_card(
        self, 
        callback: CallbackQuery, 
        images: List[ImageGeneration], 
        img_idx: int
    ):
        """Отправляет карточку изображения"""
        
        if img_idx >= len(images):
            await callback.answer("❌ Изображение не найдено", show_alert=True)
            return
        
        generation = images[img_idx]
        
        # Получаем пользователя для сохранения состояния
        user = await self.get_user_from_callback(callback)
        if user:
            # Сохраняем текущий индекс в Redis
            await gallery_cache.set_user_gallery_state(user.id, img_idx)
        
        # Формируем текст карточки
        text = self._format_image_card_text(generation, img_idx, len(images))
        
        # Формируем клавиатуру
        keyboard = build_gallery_image_keyboard(
            img_idx=img_idx,
            total_images=len(images),
            generation_id=str(generation.id),
            is_favorite=getattr(generation, 'is_favorite', False)
        )
        
        # Пытаемся загрузить и отправить изображение
        if generation.result_urls and len(generation.result_urls) > 0:
            image_url = generation.result_urls[0]
            image_data = await self._download_image(image_url)
            
            if image_data:
                await self._send_card_with_image(callback, text, keyboard, image_data)
            else:
                await self._send_card_text_only(callback, text, keyboard)
        else:
            await self._send_card_text_only(callback, text, keyboard)
    
    def _format_image_card_text(
        self, 
        generation: ImageGeneration, 
        img_idx: int, 
        total_images: int
    ) -> str:
        """Форматирует текст карточки изображения (как в оригинальном коде)"""
        
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
    
    async def _send_card_with_image(
        self, 
        callback: CallbackQuery, 
        text: str, 
        keyboard, 
        image_data: bytes
    ):
        """Отправляет карточку с изображением (обновлено под оригинальный код)"""
        
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
                # Уровень 2: Проблема с Markdown - отправляем с HTML
                logger.warning(f"Проблема с Markdown парсингом, переключаюсь на HTML: {markdown_error}")
                
                # Переформатируем для HTML
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
            else:
                logger.exception(f"Другая ошибка Telegram при отправке изображения: {markdown_error}")
                await self._send_card_text_only(callback, text, keyboard)
        except Exception as e:
            logger.exception(f"Общая ошибка отправки карточки с изображением: {e}")
            # Fallback на текстовую карточку
            await self._send_card_text_only(callback, text, keyboard)
    
    async def _send_card_text_only(self, callback: CallbackQuery, text: str, keyboard):
        """Отправляет карточку только с текстом (обновлено под оригинальный код)"""
        
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
        """Скачивает изображение по URL с автоматическим обновлением expired URL"""
        
        try:
            logger.debug(f"Попытка загрузки изображения: {url[:50]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.debug(f"✅ Изображение загружено: {len(image_data)} байт")
                        return image_data
                    elif response.status == 403:
                        # URL устарел - пытаемся обновить
                        logger.warning(f"⚠️ URL устарел (HTTP 403), пытаемся обновить: {url[:50]}...")
                        
                        updated_image_data = await self._try_refresh_minio_url(url)
                        if updated_image_data:
                            logger.info(f"✅ Изображение загружено через обновленный URL")
                            return updated_image_data
                        else:
                            logger.warning(f"❌ Не удалось обновить URL: {url[:50]}...")
                            return None
                    else:
                        logger.warning(f"❌ Ошибка загрузки изображения: HTTP {response.status} для URL {url[:50]}...")
                        return None
                        
        except Exception as e:
            logger.warning(f"❌ Ошибка скачивания изображения {url[:50]}...: {e}")
            return None
    
    async def _try_refresh_minio_url(self, old_url: str) -> Optional[bytes]:
        """Пытается обновить устаревший MinIO URL и загрузить изображение (ОПТИМИЗИРОВАННО)"""
        
        try:
            from app.services.storage.minio import MinioStorage
            import urllib.parse
            
            # Парсим старый URL чтобы извлечь bucket и object_name
            parsed_url = urllib.parse.urlparse(old_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                logger.warning(f"❌ Невозможно разобрать URL: {old_url[:50]}...")
                return None
            
            bucket = path_parts[0]
            object_name = path_parts[1].split('?')[0]  # Убираем query параметры
            
            logger.debug(f"🔄 Пытаемся обновить: bucket={bucket}, object={object_name}")
            
            storage = MinioStorage()
            
            # ✅ ОПТИМИЗАЦИЯ: Используем только работающий вариант с префиксом "generated/"
            # Из логов видно что "вариант 2" всегда работает
            correct_path = f"generated/{object_name}"
            
            logger.info(f"🔍 Используем оптимизированный путь: bucket='{bucket}', path='{correct_path}'")
            
            # Создаем новый presigned URL для правильного пути
            new_url = await storage.generate_presigned_url(
                bucket=bucket,
                object_name=correct_path,
                expires=86400  # 1 день
            )
            
            if not new_url:
                logger.warning(f"❌ Не удалось создать URL для оптимизированного пути")
                return None
            
            logger.debug(f"🆕 Оптимизированный URL создан: {new_url[:50]}...")
            
            # Пытаемся загрузить по новому URL
            async with aiohttp.ClientSession() as session:
                async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"✅ Файл найден через оптимизированный путь: bucket='{bucket}', path='{correct_path}'")
                        logger.info(f"✅ Изображение загружено: {len(image_data)} байт")
                        
                        # TODO: Обновить URL в базе данных для будущих запросов
                        # await self._update_url_in_database(old_url, new_url)
                        
                        return image_data
                    else:
                        logger.warning(f"❌ Оптимизированный путь не работает: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.exception(f"❌ Критическая ошибка обновления MinIO URL: {e}")
            return None
    
    async def _get_user_completed_images(self, user_id: UUID) -> List[ImageGeneration]:
        """Получает завершенные изображения пользователя (с кэшированием для ускорения)"""
        
        try:
            # Сначала пытаемся получить из кэша
            cached_images = await gallery_cache.get_user_images(user_id)
            if cached_images:
                logger.debug(f"Изображения получены из кэша: {len(cached_images)} штук")
                return cached_images
            
            # Если кэша нет, загружаем из БД
            logger.debug(f"Загружаем изображения из БД для пользователя {user_id}")
            
            # Получаем все генерации пользователя
            generations = await self.generation_service.get_user_generations(
                user_id=user_id,
                limit=100  # Лимит для производительности
            )
            
            # Фильтруем только завершенные генерации с результатами
            completed_images = []
            for gen in generations:
                # Проверяем статус и наличие результатов
                if (gen.status == GenerationStatus.COMPLETED and 
                    gen.result_urls and len(gen.result_urls) > 0):
                    completed_images.append(gen)
            
            # Сортируем по дате создания (новые первые)
            completed_images.sort(key=lambda x: x.created_at, reverse=True)
            
            # Сохраняем в кэш
            await gallery_cache.set_user_images(user_id, completed_images)
            
            logger.debug(f"Загружено из БД и кэшировано {len(completed_images)} завершенных изображений для пользователя {user_id}")
            return completed_images
            
        except Exception as e:
            logger.exception(f"Ошибка получения изображений пользователя {user_id}: {e}")
            return []
    
    async def _show_empty_gallery_message(self, callback: CallbackQuery):
        """Показывает сообщение о пустой галерее"""
        
        text = """🖼️ *Ваша галерея пуста*

🎨 *Создайте первое изображение!*

💡 *Что можно делать:*
• Генерировать изображения по своим промптам
• Создавать изображения по референсным фото
• Использовать готовые шаблоны стилей
• Экспериментировать с разными форматами

🚀 *Начните прямо сейчас!*"""
        
        keyboard = build_empty_gallery_keyboard()
        
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def show_full_prompt(self, callback: CallbackQuery):
        """Показывает полный промпт генерации"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id_str = data_parts[1]
            generation_id = UUID(generation_id_str)
            
            logger.info(f"🔍 Обработка callback gallery_full_prompt: {callback.data} от пользователя {callback.from_user.id}")
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                logger.warning(f"❌ Пользователь {callback.from_user.id} не найден при показе промпта")
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            logger.info(f"👤 Пользователь найден: {user.id}")
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
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

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data=f"my_gallery_return:{str(generation_id)}"),
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
                    logger.warning(f"Проблема с Markdown парсингом, переключаюсь на HTML: {markdown_error}")
                    
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