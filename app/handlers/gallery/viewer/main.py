"""
🚀 УЛЬТРАБЫСТРЫЙ просмотрщик галереи изображений
Рефакторенная версия с модульной архитектурой
"""
import asyncio
from typing import List, Optional
from uuid import UUID

from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.core.logger import get_logger
from app.database.models.generation import ImageGeneration, GenerationStatus

from ..cache import ultra_gallery_cache, ImageCacheManager
from .navigation import NavigationHandler
from .image_loader import ImageLoader
from .card_formatter import CardFormatter
from ..keyboards import build_empty_gallery_keyboard

logger = get_logger(__name__)


class GalleryViewer(BaseHandler):
    """🚀 УЛЬТРАБЫСТРЫЙ просмотрщик галереи изображений (рефакторенный)"""
    
    def __init__(self):
        # 🔥 НЕ создаем generation_service в конструкторе - он создает FAL клиента!
        # Используем ленивую инициализацию только когда действительно нужно
        self._generation_service = None
        
        # Модульные компоненты
        self.navigation_handler = NavigationHandler()
        self.image_loader = ImageLoader()
        self.card_formatter = CardFormatter()
        self.image_cache_manager = ImageCacheManager()
    
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
            images = await self.get_user_completed_images_ultra_fast(user.id)
            
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
            asyncio.create_task(self.image_cache_manager.prefetch_adjacent_images(images, img_idx))
            
            # ⚡ ПОКАЗЫВАЕМ изображение МАКСИМАЛЬНО БЫСТРО
            await self.send_image_card_ultra_fast(callback, images, img_idx, user.id)
            
            logger.info(f"⚡ Gallery shown: user {user.telegram_id}, {len(images)} images, index {img_idx}")
            
        except Exception as e:
            logger.exception(f"❌ Ошибка показа галереи: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)
    
    async def handle_image_navigation(self, callback: CallbackQuery, direction: str):
        """⚡ БЫСТРАЯ навигация (делегирует NavigationHandler)"""
        await self.navigation_handler.handle_image_navigation(callback, direction)
    
    async def send_image_card_ultra_fast(
        self, 
        callback: CallbackQuery, 
        images: List[ImageGeneration], 
        img_idx: int,
        user_id: UUID
    ):
        """⚡ МОЛНИЕНОСНАЯ отправка карточки (МАКСИМАЛЬНАЯ СКОРОСТЬ)"""
        
        generation = images[img_idx]
        
        # 🎯 ПОЛНЫЙ текст карточки (но оптимизированный)
        text = self.card_formatter.format_image_card_text_fast(generation, img_idx, len(images))
        
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
    
    async def get_user_completed_images_ultra_fast(self, user_id: UUID) -> List[ImageGeneration]:
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
    
    def _build_optimized_gallery_keyboard_v2(
        self,
        img_idx: int, 
        total_images: int, 
        generation_id: str,
        is_favorite: bool = False
    ):
        """🔥 Оптимизированная ПОЛНАЯ клавиатура галереи"""
        
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
                # ✅ ХОРОШО: У нас текстовое сообщение, добавляем фото
                await callback.message.answer_photo(
                    photo=image_file,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                logger.debug("✅ Фото добавлено к текстовому сообщению")
                
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
            image_data = await self.image_loader.download_image_ultra_fast(image_url)
            
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