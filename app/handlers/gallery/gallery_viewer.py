"""
Модуль для просмотра галереи изображений (МАКСИМАЛЬНО ОПТИМИЗИРОВАН)
"""
import aiohttp
import asyncio
from typing import List, Optional, Dict, Any, Tuple
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


class UltraFastGalleryCache:
    """
    🚀 УЛЬТРАБЫСТРЫЙ КЭШ ГАЛЕРЕИ
    - Кэширование списка изображений на 15 минут
    - Агрессивная предзагрузка (prefetch) изображений  
    - Кэширование загруженных файлов на 45 минут
    - ПОЛНОЕ избегание SQL/HTTP запросов при навигации
    """
    
    def __init__(self):
        self._images_cache = {}          # Кэш списков изображений
        self._downloaded_cache = {}      # Кэш скачанных изображений
        self._users_cache = {}           # Кэш данных пользователей
        self._prefetch_tasks = {}        # Задачи предзагрузки
        self._session_data = {}          # Данные сессии для избежания SQL
    
    async def get_user_images(self, user_id: UUID) -> Optional[List[ImageGeneration]]:
        """🎯 Получает изображения из кэша"""
        cache_key = f"user_{user_id}"
        cached_data = self._images_cache.get(cache_key)
        
        if cached_data:
            # Увеличиваем время кэша до 15 минут для лучшей производительности
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=15):
                logger.debug(f"✅ Images CACHE HIT для пользователя {user_id}: {len(cached_data['images'])} изображений")
                return cached_data['images']
        
        return None
    
    async def set_user_images(self, user_id: UUID, images: List[ImageGeneration]):
        """🎯 Сохраняет изображения в кэш"""
        cache_key = f"user_{user_id}"
        
        self._images_cache[cache_key] = {
            'images': images,
            'timestamp': datetime.now()
        }
        logger.debug(f"✅ Images CACHE SET для пользователя {user_id}: {len(images)} изображений")
    
    async def get_cached_image(self, url: str) -> Optional[bytes]:
        """🎯 Получает скачанное изображение из кэша"""
        cached_data = self._downloaded_cache.get(url)
        
        if cached_data:
            # Увеличиваем время кэша файлов до 45 минут
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=45):
                logger.debug(f"✅ IMAGE CACHE HIT: {url[:50]}... ({len(cached_data['data'])} байт)")
                return cached_data['data']
        
        return None
    
    async def set_cached_image(self, url: str, data: bytes):
        """🎯 Сохраняет скачанное изображение в кэш"""
        self._downloaded_cache[url] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"✅ IMAGE CACHE SET: {url[:50]}... ({len(data)} байт)")
    
    async def prefetch_adjacent_images(self, images: List[ImageGeneration], current_idx: int):
        """🚀 МАКСИМАЛЬНО АГРЕССИВНАЯ предзагрузка для мгновенной навигации"""
        
        prefetch_indices = []
        
        # Предзагружаем больше изображений в обе стороны (увеличено с 3 до 5)
        for offset in [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]:
            idx = current_idx + offset
            if 0 <= idx < len(images):
                prefetch_indices.append(idx)
        
        # Также предзагружаем несколько случайных изображений для лучшего покрытия
        import random
        random_indices = random.sample(range(len(images)), min(10, len(images)))
        for idx in random_indices:
            if idx not in prefetch_indices and idx != current_idx:
                prefetch_indices.append(idx)
        
        logger.debug(f"🚀 МАКСИМАЛЬНАЯ предзагрузка: {len(prefetch_indices)} изображений (current: {current_idx})")
        
        # Запускаем предзагрузку параллельно с приоритетом
        priority_tasks = []  # Соседние изображения (высокий приоритет)
        background_tasks = []  # Случайные изображения (низкий приоритет)
        
        for idx in prefetch_indices:
            generation = images[idx]
            if generation.result_urls and len(generation.result_urls) > 0:
                url = generation.result_urls[0]
                
                # Проверяем что изображение еще не кэшировано
                if url not in self._downloaded_cache:
                    task_key = f"prefetch_{url}"
                    
                    # Избегаем дублированных задач предзагрузки
                    if task_key not in self._prefetch_tasks:
                        # Определяем приоритет (соседние vs случайные)
                        is_adjacent = abs(idx - current_idx) <= 5
                        
                        if is_adjacent:
                            task = asyncio.create_task(
                                self._prefetch_single_image_priority(url, high_priority=True)
                            )
                            priority_tasks.append(task)
                        else:
                            task = asyncio.create_task(
                                self._prefetch_single_image_priority(url, high_priority=False)
                            )
                            background_tasks.append(task)
                        
                        self._prefetch_tasks[task_key] = task
        
        # Ждем завершения приоритетных задач (не блокируя UI)
        if priority_tasks:
            asyncio.create_task(self._wait_priority_prefetch(priority_tasks))
    
    async def _wait_priority_prefetch(self, priority_tasks):
        """Ждет завершения приоритетных задач предзагрузки"""
        try:
            # Ждем максимум 2 секунды для приоритетных изображений
            await asyncio.wait_for(
                asyncio.gather(*priority_tasks, return_exceptions=True),
                timeout=2.0
            )
            logger.debug("✅ Приоритетная предзагрузка завершена")
        except asyncio.TimeoutError:
            logger.debug("⏱️ Таймаут приоритетной предзагрузки (это нормально)")
        except Exception as e:
            logger.debug(f"❌ Ошибка приоритетной предзагрузки: {e}")
    
    async def _prefetch_single_image_priority(self, url: str, high_priority: bool = True):
        """🔄 Предзагружает одно изображение с приоритизацией"""
        try:
            # Проверяем что изображение еще не кэшировано
            cached = await self.get_cached_image(url)
            if cached:
                return
            
            # Настраиваем таймаут в зависимости от приоритета
            timeout = 3 if high_priority else 8
            
            # Загружаем изображение
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        data = await response.read()
                        await self.set_cached_image(url, data)
                        priority_text = "HIGH" if high_priority else "LOW"
                        logger.debug(f"🚀 PREFETCH {priority_text}: {url[:50]}... ({len(data)} байт)")
                    elif response.status == 403:
                        # URL устарел - пытаемся обновить только для высокого приоритета
                        if high_priority:
                            updated_data = await self._try_refresh_minio_url_ultra_fast(url)
                            if updated_data:
                                await self.set_cached_image(url, updated_data)
                                logger.debug(f"🚀 PREFETCH HIGH REFRESHED: {url[:50]}... ({len(updated_data)} байт)")
                    else:
                        logger.debug(f"🚀 PREFETCH FAILED: {url[:50]}... (HTTP {response.status})")
            
        except asyncio.TimeoutError:
            priority_text = "HIGH" if high_priority else "LOW"
            logger.debug(f"⏱️ PREFETCH {priority_text} TIMEOUT: {url[:50]}...")
        except Exception as e:
            logger.debug(f"🚀 PREFETCH ERROR: {url[:50]}... - {e}")
        finally:
            # Удаляем задачу из списка активных
            task_key = f"prefetch_{url}"
            if task_key in self._prefetch_tasks:
                del self._prefetch_tasks[task_key]
    
    async def set_session_data(self, user_id: UUID, data: Dict[str, Any]):
        """🎯 Сохраняет данные сессии для избежания SQL запросов"""
        self._session_data[user_id] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    async def get_session_data(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """🎯 Получает данные сессии"""
        cached_data = self._session_data.get(user_id)
        
        if cached_data:
            # Проверяем возраст кэша (30 минут для сессии)
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=30):
                return cached_data['data']
        
        return None
    
    async def cache_user_data(self, user_id: UUID, user_data: Any):
        """🎯 Кэширует данные пользователя"""
        self._users_cache[user_id] = {
            'data': user_data,
            'timestamp': datetime.now()
        }
    
    async def get_cached_user_data(self, user_id: UUID) -> Optional[Any]:
        """🎯 Получает данные пользователя из кэша"""
        cached_data = self._users_cache.get(user_id)
        
        if cached_data:
            # Проверяем возраст кэша (15 минут для пользователей)
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=15):
                return cached_data['data']
        
        return None
    
    async def clear_all_cache(self, user_id: UUID):
        """🧹 Очищает весь кэш пользователя"""
        cache_key = f"user_{user_id}"
        if cache_key in self._images_cache:
            del self._images_cache[cache_key]
        
        if user_id in self._users_cache:
            del self._users_cache[user_id]
        
        if user_id in self._session_data:
            del self._session_data[user_id]
    
    async def set_user_gallery_state(self, user_id: UUID, current_index: int):
        """🎯 Сохраняет текущий индекс галереи в Redis (fire-and-forget)"""
        try:
            from app.core.di import get_redis
            from datetime import datetime
            import json
            
            redis_client = await get_redis()
            
            state_key = f"gallery_state:{user_id}"
            state_data = {
                'current_index': current_index,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем БЕЗ ОЖИДАНИЯ (fire-and-forget)
            asyncio.create_task(redis_client.setex(
                state_key,
                1800,  # 30 минут TTL
                json.dumps(state_data)
            ))
            
            logger.debug(f"🎯 Gallery state ASYNC SET: user {user_id}, index {current_index}")
            
        except Exception as e:
            logger.debug(f"⚠️ Redis state error (ignored): {e}")
    
    async def get_user_gallery_state(self, user_id: UUID) -> Optional[int]:
        """🎯 Получает текущий индекс галереи из Redis"""
        try:
            from app.core.di import get_redis
            import json
            
            redis_client = await get_redis()
            
            state_key = f"gallery_state:{user_id}"
            cached_state = await redis_client.get(state_key)
            
            if cached_state:
                state_data = json.loads(cached_state)
                current_index = state_data.get('current_index', 0)
                
                logger.debug(f"🎯 Gallery state RESTORED: user {user_id}, index {current_index}")
                return current_index
            
        except Exception as e:
            logger.debug(f"⚠️ Redis state error (ignored): {e}")
        
        return None


# 🚀 Глобальный экземпляр ультрабыстрого кэша
ultra_gallery_cache = UltraFastGalleryCache()


class GalleryViewer(BaseHandler):
    """🚀 УЛЬТРАБЫСТРЫЙ просмотрщик галереи изображений"""
    
    def __init__(self):
        # 🔥 НЕ создаем generation_service в конструкторе - он создает FAL клиента!
        # Используем ленивую инициализацию только когда действительно нужно
        self._generation_service = None
    
    @property
    def generation_service(self):
        """Ленивая инициализация сервиса генерации"""
        if self._generation_service is None:
            from app.services.generation.generation_service import ImageGenerationService
            self._generation_service = ImageGenerationService()
        return self._generation_service
    
    @require_user()
    async def show_gallery_main(
        self, 
        callback: CallbackQuery, 
        state: FSMContext,
        user=None,
        start_index: Optional[int] = None
    ):
        """🚀 БЫСТРЫЙ показ галереи с надежным кэшированием"""
        
        try:
            # 🔥 Очищаем состояние БЕЗ ожидания (fire-and-forget)
            asyncio.create_task(self.safe_clear_state(state))
            
            # 🎯 СИНХРОННО сохраняем сессионные данные (чтобы они точно были при навигации)
            await ultra_gallery_cache.set_session_data(user.id, {
                'telegram_id': user.telegram_id,
                'id': str(user.id),
                'username': user.username or '',
                'first_name': user.first_name
            })
            
            # 🎯 Кэшируем пользователя асинхронно
            asyncio.create_task(ultra_gallery_cache.cache_user_data(user.id, user))
            
            # 🔥 ПРЯМОЕ получение изображений (БЕЗ generation_service)
            images = await self._get_user_completed_images_ultra_fast(user.id)
            
            if not images:
                await self._show_empty_gallery_message(callback)
                return
            
            # Определяем стартовый индекс БЕЗ лишних операций
            if start_index is not None:
                img_idx = max(0, min(start_index, len(images) - 1))
            else:
                # Быстрое получение из Redis (НЕ блокируем UI)
                try:
                    saved_index = await ultra_gallery_cache.get_user_gallery_state(user.id)
                    img_idx = saved_index if (saved_index is not None and saved_index < len(images)) else 0
                except:
                    img_idx = 0
            
            # 🚀 АГРЕССИВНАЯ предзагрузка (неблокирующе)
            asyncio.create_task(ultra_gallery_cache.prefetch_adjacent_images(images, img_idx))
            
            # ⚡ ПОКАЗЫВАЕМ изображение МАКСИМАЛЬНО БЫСТРО
            await self._send_image_card_ultra_ultra_fast(callback, images, img_idx, user.id)
            
            logger.info(f"⚡ Gallery shown: user {user.telegram_id}, {len(images)} images, index {img_idx}")
            
        except Exception as e:
            logger.exception(f"❌ Ошибка показа галереи: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)
    
    async def handle_image_navigation(self, callback: CallbackQuery, direction: str):
        """⚡ БЫСТРАЯ навигация с надежными fallback"""
        
        try:
            # Извлекаем данные из callback_data
            data_parts = callback.data.split(":")
            current_idx = int(data_parts[1])
            
            # 🔥 УРОВЕНЬ 1: Быстрый поиск в сессионном кэше
            user_id = None
            telegram_id = callback.from_user.id
            
            for cached_user_id, session_cache in ultra_gallery_cache._session_data.items():
                session_data = session_cache.get('data', {})
                if (session_data.get('telegram_id') == telegram_id and
                    datetime.now() - session_cache['timestamp'] < timedelta(minutes=30)):
                    user_id = cached_user_id
                    break
            
            # 🔥 УРОВЕНЬ 2: Если сессии нет - восстанавливаем через SQL (fallback)
            if not user_id:
                logger.debug(f"Session cache miss, fallback to SQL for user {telegram_id}")
                user = await self.get_user_from_callback(callback, show_error=False)
                if not user:
                    await callback.answer("🔄 Пожалуйста, перезайдите в галерею", show_alert=True)
                    return
                
                user_id = user.id
                # Восстанавливаем сессию для следующих кликов
                await ultra_gallery_cache.set_session_data(user_id, {
                    'telegram_id': telegram_id,
                    'id': str(user_id),
                    'username': user.username or '',
                    'first_name': user.first_name
                })
                logger.debug(f"Session restored for user {user_id}")
            
            # 🔥 УРОВЕНЬ 3: Получаем изображения (кэш или SQL fallback)
            images = await ultra_gallery_cache.get_user_images(user_id)
            if not images:
                logger.debug(f"Images cache miss, loading from DB for user {user_id}")
                images = await self._get_user_completed_images_ultra_fast(user_id)
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
            
            # 🚀 АГРЕССИВНО ПРЕДЗАГРУЖАЕМ следующие изображения (неблокирующе)
            asyncio.create_task(ultra_gallery_cache.prefetch_adjacent_images(images, new_idx))
            
            # ⚡ ПОКАЗЫВАЕМ новое изображение быстро
            await self._send_image_card_ultra_ultra_fast(callback, images, new_idx, user_id)
            
            logger.debug(f"⚡ Navigation: {current_idx} → {new_idx}")
            
        except Exception as e:
            logger.exception(f"❌ Ошибка навигации: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _send_image_card_ultra_ultra_fast(
        self, 
        callback: CallbackQuery, 
        images: List[ImageGeneration], 
        img_idx: int,
        user_id: UUID
    ):
        """⚡ МОЛНИЕНОСНАЯ отправка карточки (МАКСИМАЛЬНАЯ СКОРОСТЬ)"""
        
        generation = images[img_idx]
        
        # 🎯 ПОЛНЫЙ текст карточки (но оптимизированный)
        text = self._format_image_card_text_fast(generation, img_idx, len(images))
        
        # 🔥 ПОЛНАЯ клавиатура (восстановленная функциональность)
        keyboard = self._build_optimized_gallery_keyboard_v2(
            img_idx=img_idx,
            total_images=len(images),
            generation_id=str(generation.id),
            is_favorite=getattr(generation, 'is_favorite', False)
        )
        
        # ⚡ ПРЯМАЯ загрузка из кэша (БЕЗ лишних проверок)
        if generation.result_urls:
            image_url = generation.result_urls[0]
            image_data = await ultra_gallery_cache.get_cached_image(image_url)
            
            if image_data:
                # МГНОВЕННАЯ отправка
                await self._send_card_with_image_lightning_fast(callback, text, keyboard, image_data)
                # Сохраняем состояние в фоне БЕЗ ожидания
                asyncio.create_task(ultra_gallery_cache.set_user_gallery_state(user_id, img_idx))
                return
        
        # Fallback: показываем загрузку
        await self._send_card_text_loading(callback, text, keyboard)
        
        # Сохраняем состояние и загружаем контент в фоне
        asyncio.create_task(ultra_gallery_cache.set_user_gallery_state(user_id, img_idx))
        if generation.result_urls:
            asyncio.create_task(self._async_load_and_update_image(callback, generation.result_urls[0], text, keyboard))
    
    def _format_image_card_text_fast(
        self, 
        generation: ImageGeneration, 
        img_idx: int, 
        total_images: int
    ) -> str:
        """Быстрое форматирование текста карточки"""
        
        # Безопасное название аватара
        avatar_name = generation.avatar.name if generation.avatar and generation.avatar.name else "Неизвестно"
        
        # Статус избранного
        favorite_status = "❤️ В избранном" if getattr(generation, 'is_favorite', False) else ""
        
        # Размер
        aspect_ratio = getattr(generation, 'aspect_ratio', '1:1')
        
        # Быстрая сборка текста
        text_parts = [
            f"🖼️ *Изображение {img_idx + 1} из {total_images}*",
            "",
            f"🎭 *Аватар:* {avatar_name}",
            f"📐 *Размер:* {aspect_ratio}"
        ]
        
        if favorite_status:
            text_parts.append("")
            text_parts.append(favorite_status)
        
        return "\n".join(text_parts)
    
    def _build_optimized_gallery_keyboard_v2(
        self,
        img_idx: int, 
        total_images: int, 
        generation_id: str,
        is_favorite: bool = False
    ):
        """🔥 Оптимизированная ПОЛНАЯ клавиатура галереи"""
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        buttons = []
        
        # 🔝 БЛОК 1: Фильтры и статистика
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
        
        # ⭐ БЛОК 4: Избранное и управление
        action_row = []
        
        favorite_text = "❤️ Убрать из избранного" if is_favorite else "🤍 В избранное"
        action_row.append(InlineKeyboardButton(text=favorite_text, callback_data=f"gallery_favorite:{generation_id}"))
        action_row.append(InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"gallery_delete:{generation_id}"))
        
        buttons.append(action_row)
        
        # 🔙 БЛОК 5: Навигация назад
        back_row = [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
        buttons.append(back_row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def _send_card_with_image_lightning_fast(
        self, 
        callback: CallbackQuery, 
        text: str, 
        keyboard, 
        image_data: bytes
    ):
        """⚡ БЫСТРАЯ отправка изображения БЕЗ удаления сообщений"""
        
        try:
            image_file = BufferedInputFile(image_data, filename="img.jpg")
            
            if callback.message.photo:
                # ✅ ИДЕАЛЬНО: Редактируем существующее фото (БЕЗ мерцания)
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=image_file, caption=text, parse_mode="Markdown"),
                    reply_markup=keyboard
                )
                logger.debug("✅ Изображение обновлено через edit_media (без мерцания)")
                
            elif callback.message.text:
                # ✅ ХОРОШО: У нас текстовое сообщение, редактируем на фото
                try:
                    await callback.message.edit_text(
                        text="🔄 Обновление изображения...",
                        reply_markup=None
                    )
                    await asyncio.sleep(0.1)  # Микро-пауза для плавности
                    
                    # Теперь отправляем фото как ответ на это сообщение
                    await callback.message.answer_photo(
                        photo=image_file,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    logger.debug("✅ Фото добавлено к текстовому сообщению")
                    
                except Exception as edit_error:
                    logger.debug(f"Не удалось отредактировать текст, отправляю новое фото: {edit_error}")
                    await callback.message.answer_photo(
                        photo=image_file,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
            else:
                # Неизвестный тип сообщения - отправляем новое
                await callback.message.answer_photo(
                    photo=image_file,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug("✅ Новое фото отправлено")
                
        except TelegramBadRequest as e:
            if "media" in str(e).lower() or "photo" in str(e).lower():
                logger.warning(f"Ошибка медиа Telegram: {e}")
                # Fallback на текст с кнопкой "Показать изображение"
                await self._send_image_fallback_with_button(callback, text, keyboard, image_data)
            else:
                logger.debug(f"Другая ошибка Telegram: {e}")
                await self._send_card_text_loading(callback, text, keyboard)
                
        except Exception as e:
            logger.debug(f"Общая ошибка отправки изображения: {e}")
            await self._send_card_text_loading(callback, text, keyboard)
    
    async def _send_image_fallback_with_button(
        self, 
        callback: CallbackQuery, 
        text: str, 
        keyboard, 
        image_data: bytes
    ):
        """Fallback: текст + кнопка для повторной попытки показа изображения"""
        
        try:
            fallback_text = f"{text}\n\n📷 *Изображение готово к просмотру*\n💡 _Нажмите кнопку ниже для показа_"
            
            # Добавляем кнопку "Показать изображение" к клавиатуре
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            # Копируем существующие кнопки
            new_buttons = []
            if hasattr(keyboard, 'inline_keyboard'):
                new_buttons = [row[:] for row in keyboard.inline_keyboard]
            
            # Добавляем кнопку показа изображения в начало
            show_image_button = [
                InlineKeyboardButton(text="📷 Показать изображение", callback_data="show_current_image")
            ]
            new_buttons.insert(0, show_image_button)
            
            fallback_keyboard = InlineKeyboardMarkup(inline_keyboard=new_buttons)
            
            if callback.message.photo:
                # Заменяем фото на текст
                await callback.message.edit_caption(
                    caption=fallback_text,
                    reply_markup=fallback_keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Редактируем текст
                await callback.message.edit_text(
                    text=fallback_text,
                    reply_markup=fallback_keyboard,
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.debug(f"Ошибка fallback с кнопкой: {e}")
            await self._send_card_text_loading(callback, text, keyboard)
    
    async def _send_card_text_loading(self, callback: CallbackQuery, text: str, keyboard):
        """Отправляет карточку с индикатором загрузки БЕЗ удаления сообщений"""
        
        loading_text = f"{text}\n\n⏳ Загрузка изображения..."
        
        try:
            if callback.message.photo:
                # ✅ Редактируем подпись под фото (оставляем фото)
                await callback.message.edit_caption(
                    caption=loading_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug("✅ Обновлена подпись под фото (loading)")
                
            elif callback.message.text:
                # ✅ Редактируем текст сообщения
                await callback.message.edit_text(
                    text=loading_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug("✅ Обновлен текст сообщения (loading)")
                
            else:
                # Отправляем новое текстовое сообщение
                await callback.message.answer(
                    text=loading_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug("✅ Отправлено новое текстовое сообщение (loading)")
                
        except TelegramBadRequest as e:
            if "parse entities" in str(e):
                # Проблема с Markdown - повторяем без форматирования
                try:
                    if callback.message.photo:
                        await callback.message.edit_caption(
                            caption=loading_text.replace("*", "").replace("_", ""),
                            reply_markup=keyboard
                        )
                    elif callback.message.text:
                        await callback.message.edit_text(
                            text=loading_text.replace("*", "").replace("_", ""),
                            reply_markup=keyboard
                        )
                    else:
                        await callback.message.answer(
                            text=loading_text.replace("*", "").replace("_", ""),
                            reply_markup=keyboard
                        )
                except Exception:
                    await callback.answer("❌ Ошибка отображения", show_alert=True)
            else:
                logger.debug(f"Ошибка обновления текста loading: {e}")
                await callback.answer("⏳ Загружается...", show_alert=False)
                
        except Exception as e:
            logger.debug(f"Общая ошибка loading: {e}")
            await callback.answer("⏳ Загружается...", show_alert=False)
    
    async def _async_load_and_update_image(self, callback: CallbackQuery, image_url: str, text: str, keyboard):
        """Асинхронно загружает и обновляет изображение БЕЗ удаления сообщений"""
        
        try:
            # Быстрая загрузка с коротким таймаутом
            image_data = await self._download_image_ultra_fast(image_url)
            
            if image_data:
                # ✅ Обновляем сообщение с изображением (БЕЗ удаления)
                image_file = BufferedInputFile(image_data, filename="img.jpg")
                
                if callback.message.photo:
                    # Редактируем существующее фото
                    await callback.message.edit_media(
                        media=InputMediaPhoto(media=image_file, caption=text, parse_mode="Markdown"),
                        reply_markup=keyboard
                    )
                    logger.debug("✅ Изображение обновлено асинхронно через edit_media")
                    
                elif callback.message.text:
                    # Текстовое сообщение - добавляем фото как ответ
                    await callback.message.answer_photo(
                        photo=image_file,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    logger.debug("✅ Фото добавлено к текстовому сообщению асинхронно")
                else:
                    # Отправляем новое фото
                    await callback.message.answer_photo(
                        photo=image_file,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    logger.debug("✅ Новое фото отправлено асинхронно")
                    
            else:
                # Не удалось загрузить - обновляем текст с ошибкой
                error_text = f"{text}\n\n❌ *Изображение недоступно*\n💡 _Попробуйте переключить на другое изображение_"
                
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=error_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                elif callback.message.text:
                    await callback.message.edit_text(
                        text=error_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    
                logger.debug("❌ Изображение недоступно - показан текст с ошибкой")
                
        except Exception as e:
            logger.debug(f"Ошибка асинхронной загрузки изображения: {e}")
            # Игнорируем ошибки фоновой загрузки чтобы не нарушать UX
    
    async def _download_image_ultra_fast(self, url: str) -> Optional[bytes]:
        """🚀 УЛЬТРАБЫСТРАЯ загрузка изображения с множественными попытками"""
        
        try:
            # 🎯 СНАЧАЛА проверяем кэш
            cached_data = await ultra_gallery_cache.get_cached_image(url)
            if cached_data:
                logger.debug(f"🚀 ULTRA FAST image load from cache: {len(cached_data)} bytes")
                return cached_data
            
            logger.debug(f"🔄 Loading image from network: {url[:50]}...")
            
            # ПОПЫТКА 1: Загружаем оригинальный URL
            image_data = await self._try_download_url(url)
            if image_data:
                await ultra_gallery_cache.set_cached_image(url, image_data)
                logger.debug(f"✅ Image loaded and cached: {len(image_data)} bytes")
                return image_data
            
            # ПОПЫТКА 2: URL устарел - обновляем через MinIO
            logger.debug(f"⚠️ Original URL failed, trying refresh: {url[:50]}...")
            updated_data = await self._try_refresh_minio_url_ultra_fast(url)
            if updated_data:
                await ultra_gallery_cache.set_cached_image(url, updated_data)
                logger.debug(f"✅ Image refreshed and cached: {len(updated_data)} bytes")
                return updated_data
            
            # ПОПЫТКА 3: Пробуем варианты путей
            logger.debug(f"⚠️ Trying alternative URL paths: {url[:50]}...")
            alternative_data = await self._try_alternative_paths(url)
            if alternative_data:
                await ultra_gallery_cache.set_cached_image(url, alternative_data)
                logger.debug(f"✅ Image loaded from alternative path: {len(alternative_data)} bytes")
                return alternative_data
            
            logger.warning(f"❌ All attempts failed for URL: {url[:50]}...")
            return None
                        
        except Exception as e:
            logger.debug(f"❌ Image load error: {url[:50]}... - {e}")
            return None
    
    async def _try_download_url(self, url: str, timeout: int = 5) -> Optional[bytes]:
        """Попытка загрузки URL с таймаутом"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status == 403:
                        logger.debug(f"URL expired (403): {url[:50]}...")
                        return None
                    else:
                        logger.debug(f"HTTP {response.status}: {url[:50]}...")
                        return None
        except asyncio.TimeoutError:
            logger.debug(f"Timeout loading: {url[:50]}...")
            return None
        except Exception as e:
            logger.debug(f"Error loading: {url[:50]}... - {e}")
            return None
    
    async def _try_alternative_paths(self, original_url: str) -> Optional[bytes]:
        """Пробует альтернативные пути для загрузки изображения"""
        try:
            from app.services.storage.minio import MinioStorage
            import urllib.parse
            
            # Парсим URL
            parsed_url = urllib.parse.urlparse(original_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                return None
            
            bucket = path_parts[0]
            object_name = path_parts[1].split('?')[0]
            
            storage = MinioStorage()
            
            # Варианты путей для поиска
            path_variants = [
                object_name,                        # Оригинальный путь
                f"generated/{object_name}",         # С префиксом generated/
                object_name.replace("generated/", "") if "generated/" in object_name else f"images/{object_name}",
            ]
            
            for variant_path in path_variants:
                try:
                    # Проверяем существование файла
                    if hasattr(storage, 'file_exists'):
                        exists = await storage.file_exists(bucket, variant_path)
                        if not exists:
                            continue
                    
                    # Создаем новый URL
                    new_url = await storage.generate_presigned_url(
                        bucket=bucket,
                        object_name=variant_path,
                        expires=3600
                    )
                    
                    if new_url:
                        # Пробуем загрузить
                        image_data = await self._try_download_url(new_url, timeout=3)
                        if image_data:
                            logger.debug(f"✅ Alternative path worked: {variant_path}")
                            return image_data
                            
                except Exception as variant_error:
                    logger.debug(f"Variant {variant_path} failed: {variant_error}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Alternative paths error: {e}")
            return None
    
    async def _try_refresh_minio_url_ultra_fast(self, old_url: str) -> Optional[bytes]:
        """🚀 УЛЬТРАБЫСТРОЕ обновление устаревшего MinIO URL"""
        
        try:
            from app.services.storage.minio import MinioStorage
            import urllib.parse
            
            # Парсим URL
            parsed_url = urllib.parse.urlparse(old_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                return None
            
            bucket = path_parts[0]
            object_name = path_parts[1].split('?')[0]
            
            # 🚀 ИСПОЛЬЗУЕМ ТОЛЬКО работающий путь (из логов - "вариант 2")
            correct_path = f"generated/{object_name}"
            
            storage = MinioStorage()
            
            # Создаем новый URL с коротким временем жизни для скорости
            new_url = await storage.generate_presigned_url(
                bucket=bucket,
                object_name=correct_path,
                expires=3600  # 1 час (вместо суток)
            )
            
            if not new_url:
                return None
            
            # Загружаем по новому URL с коротким таймаутом
            async with aiohttp.ClientSession() as session:
                async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.debug(f"🚀 ULTRA FAST MinIO refresh: {len(image_data)} bytes")
                        return image_data
                    else:
                        return None
                        
        except Exception as e:
            logger.debug(f"❌ MinIO refresh error (ignored): {e}")
            return None
    
    async def _get_user_completed_images_ultra_fast(self, user_id: UUID) -> List[ImageGeneration]:
        """🚀 УЛЬТРАБЫСТРОЕ получение изображений (БЕЗ создания FAL клиента)"""
        
        try:
            # 🎯 СНАЧАЛА проверяем кэш
            cached_images = await ultra_gallery_cache.get_user_images(user_id)
            if cached_images:
                logger.debug(f"🚀 ULTRA FAST images from cache: {len(cached_images)} images")
                return cached_images
            
            # 🔥 ПРЯМОЙ запрос к БД (БЕЗ generation_service и FAL клиента)
            logger.debug(f"🔄 Direct DB query for user {user_id}")
            
            from app.core.database import get_session
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            async with get_session() as session:
                # Прямой запрос с оптимизированной загрузкой
                stmt = (
                    select(ImageGeneration)
                    .options(selectinload(ImageGeneration.avatar))
                    .where(
                        ImageGeneration.user_id == user_id,
                        ImageGeneration.status == GenerationStatus.COMPLETED,
                        ImageGeneration.result_urls.isnot(None)
                    )
                    .order_by(ImageGeneration.created_at.desc())
                    .limit(150)
                )
                
                result = await session.execute(stmt)
                generations = result.scalars().all()
                
                # Фильтруем завершенные с результатами
                completed_images = [
                    gen for gen in generations
                    if (gen.result_urls and len(gen.result_urls) > 0)
                ]
            
            # 🎯 КЭШИРУЕМ на 15 минут
            await ultra_gallery_cache.set_user_images(user_id, completed_images)
            
            logger.debug(f"🚀 ULTRA FAST direct DB load: {len(completed_images)} images")
            return completed_images
            
        except Exception as e:
            logger.exception(f"❌ Ошибка получения изображений: {e}")
            return []

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
    
    async def _send_card_with_image_optimized(
        self, 
        callback: CallbackQuery, 
        text: str, 
        keyboard, 
        image_data: bytes
    ):
        """🚀 ОПТИМИЗИРОВАННАЯ отправка карточки с изображением"""
        
        try:
            image_file = BufferedInputFile(image_data, filename="gallery_image.jpg")
            
            # 🎯 ПРЯМОЕ редактирование медиа (самый быстрый способ)
            if callback.message.photo:
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=image_file, caption=text, parse_mode="Markdown"),
                    reply_markup=keyboard
                )
            else:
                # Удаляем и отправляем новое (быстро)
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
                # Fallback без Markdown
                logger.debug(f"Markdown error, using plain text: {markdown_error}")
                
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
                logger.debug(f"Other Telegram error, fallback to text: {markdown_error}")
                await self._send_card_text_only(callback, text, keyboard)
        except Exception as e:
            logger.debug(f"Image send error, fallback to text: {e}")
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

    def _build_optimized_gallery_keyboard(
        self,
        img_idx: int, 
        total_images: int, 
        generation_id: str,
        is_favorite: bool = False,
        user_id: str = ""
    ):
        """🔥 Строит оптимизированную клавиатуру БЕЗ SQL зависимостей"""
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        buttons = []
        
        # 🔝 БЛОК 1: Фильтры и навигация по галерее (наверху)
        top_row = [
            InlineKeyboardButton(text="🔍 Фильтры", callback_data="gallery_filters"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="gallery_stats")
        ]
        buttons.append(top_row)
        
        # 🔄 БЛОК 2: Навигация по изображениям (БЕЗ user_id в callback - не нужно)
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
        
        # ⭐ БЛОК 4: Избранное и управление
        action_row = []
        
        favorite_text = "❤️ Убрать из избранного" if is_favorite else "🤍 В избранное"
        action_row.append(InlineKeyboardButton(text=favorite_text, callback_data=f"gallery_favorite:{generation_id}"))
        action_row.append(InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"gallery_delete:{generation_id}"))
        
        buttons.append(action_row)
        
        # 🔙 БЛОК 5: Навигация назад
        back_row = [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
        buttons.append(back_row)
        
        return InlineKeyboardMarkup(inline_keyboard=buttons) 