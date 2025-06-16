"""
Обработчик фильтров галереи
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from app.core.logger import get_logger
from app.services.gallery_service import gallery_service
from app.handlers.gallery.states import GalleryFilterStates, GalleryFilterData, GalleryData, gallery_state_manager
from .gallery_viewer import GalleryViewer
from .gallery_manager import GalleryManager
from app.shared.utils.telegram_utils import safe_edit_callback_message

logger = get_logger(__name__)

router = Router()

# Создаем экземпляры обработчиков
gallery_viewer = GalleryViewer()
gallery_manager = GalleryManager()


class GalleryFilterHandler:
    """Обработчик фильтров галереи"""
    
    def __init__(self):
        self.gallery_viewer = GalleryViewer()
        self.gallery_manager = GalleryManager()
    
    async def _save_filters_to_cache(self, telegram_id: int, filters: dict):
        """Сохраняет фильтры в кэш для навигации"""
        try:
            # Получаем user_id по telegram_id
            from app.core.di import get_user_service
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(telegram_id)
                if not user:
                    return
                
                # Сохраняем в Redis
                from app.core.di import get_redis
                import json
                
                redis = await get_redis()
                cache_key = f"gallery:active_filters:{user.id}"
                
                # Получаем существующие фильтры и обновляем
                existing_filters_json = await redis.get(cache_key)
                if existing_filters_json:
                    existing_filters = json.loads(existing_filters_json)
                    existing_filters.update(filters)
                else:
                    existing_filters = filters
                
                # Сохраняем обновленные фильтры
                await redis.setex(cache_key, 3600, json.dumps(existing_filters))  # 1 час
                logger.debug(f"🔍 Фильтры сохранены в кэш: {existing_filters}")
                
        except Exception as e:
            logger.exception(f"Ошибка сохранения фильтров в кэш: {e}")
    
    async def show_gallery_with_type_filter(self, callback: CallbackQuery, state: FSMContext, generation_type: str):
        """Показывает галерею с фильтром по типу"""
        try:
            # ВАЖНО: Устанавливаем фильтр в состояние ДО показа галереи
            await state.update_data(generation_type=generation_type)
            
            # Также сохраняем фильтры в кэш для навигации
            await self._save_filters_to_cache(callback.from_user.id, {'generation_type': generation_type})
            
            from .viewer.main import GalleryViewer
            gallery_viewer = GalleryViewer()
            
            # Показываем галерею с фильтром
            await gallery_viewer.show_gallery_main(callback, state)
            
            logger.info(f"✅ Показана галерея с фильтром по типу: {generation_type}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа галереи с фильтром по типу: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_date_filter_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню фильтрации по дате"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="gallery_date:today"),
                InlineKeyboardButton(text="📅 Вчера", callback_data="gallery_date:yesterday")
            ],
            [
                InlineKeyboardButton(text="📅 За неделю", callback_data="gallery_date:week"),
                InlineKeyboardButton(text="📅 За месяц", callback_data="gallery_date:month")
            ],
            [
                InlineKeyboardButton(text="📅 Свой период", callback_data="gallery_date:custom"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="gallery_all")
            ]
        ])
        
        await safe_edit_callback_message(
            callback,
            text="📅 **Фильтр по дате**\n\nВыберите период для просмотра изображений:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def show_filter_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню фильтров с отображением активных фильтров"""
        
        # Получаем текущие фильтры из состояния
        state_data = await state.get_data()
        filters = {
            'generation_type': state_data.get('generation_type'),
            'start_date': state_data.get('start_date'),
            'end_date': state_data.get('end_date')
        }
        
        # Формируем текст с отображением активных фильтров
        filter_info = []
        if filters.get('generation_type'):
            if filters['generation_type'] == 'avatar':
                filter_info.append("👤 Фото со мной")
            elif filters['generation_type'] == 'imagen4':
                filter_info.append("🎨 Изображения")
        
        if filters.get('start_date') or filters.get('end_date'):
            filter_info.append("📅 По дате")
        
        if filter_info:
            filter_text = f"🔍 **Активные фильтры:**\n• {chr(10).join(filter_info)}\n\n"
        else:
            filter_text = ""
        
        text = f"{filter_text}🔍 **Фильтры галереи**\n\nВыберите тип фильтрации:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎭 По типу", callback_data="gallery_filter_type"),
                InlineKeyboardButton(text="📅 По дате", callback_data="gallery_filter_date")
            ],
            [
                InlineKeyboardButton(text="🔄 Сбросить", callback_data="gallery_reset_filters"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="all_photos")
            ]
        ])
        
        await safe_edit_callback_message(
            callback,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def show_gallery_with_date_filter(self, callback: CallbackQuery, state: FSMContext, start_date, end_date):
        """Показывает галерею с фильтром по дате"""
        try:
            # ВАЖНО: Фильтры уже должны быть установлены в состояние в handle_date_filter
            # Но проверим и установим еще раз для надежности
            await state.update_data(
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )
            
            # Также сохраняем фильтры в кэш для навигации
            date_filters = {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
            await self._save_filters_to_cache(callback.from_user.id, date_filters)
            
            from .viewer.main import GalleryViewer
            gallery_viewer = GalleryViewer()
            
            # Показываем галерею с фильтром
            await gallery_viewer.show_gallery_main(callback, state)
            
            logger.info(f"✅ Показана галерея с фильтром по дате: {start_date} - {end_date}")
            
        except Exception as e:
            logger.exception(f"Ошибка показа галереи с фильтром по дате: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
gallery_filter_handler = GalleryFilterHandler()

# ==================== ФИЛЬТРЫ ПО ТИПУ ====================

@router.callback_query(F.data == "gallery_filter_type")
async def show_type_filter_menu(callback: CallbackQuery, state: FSMContext):
    """Показывает меню фильтрации по типу"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Фото со мной", callback_data="gallery_type:avatar"),
            InlineKeyboardButton(text="🎨 Изображения", callback_data="gallery_type:imagen4")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="all_photos")
        ]
    ])
    
    await safe_edit_callback_message(
        callback,
        text="Выберите тип изображений:",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("gallery_type:"))
async def handle_type_filter(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор типа изображений"""
    try:
        # Получаем тип из callback_data
        generation_type = callback.data.split(":")[1]
        
        # Сохраняем фильтр в состоянии
        await state.update_data(generation_type=generation_type)
        
        # Показываем галерею с фильтром
        await gallery_filter_handler.show_gallery_with_type_filter(callback, state, generation_type)
        
    except Exception as e:
        logger.exception(f"Ошибка при фильтрации по типу: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# ==================== ФИЛЬТРЫ ПО ДАТЕ ====================

@router.callback_query(F.data == "gallery_filter_date")
async def show_date_filter_menu(callback: CallbackQuery, state: FSMContext):
    """Показывает меню фильтрации по дате"""
    await gallery_filter_handler.show_date_filter_menu(callback, state)

@router.callback_query(F.data.startswith("gallery_date:"))
async def handle_date_filter(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор фильтра по дате"""
    try:
        # Получаем период из callback_data
        period = callback.data.split(":")[1]
        
        from datetime import datetime, timedelta
        now = datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period == "week":
            start_date = now - timedelta(days=7)
            end_date = now
        elif period == "month":
            start_date = now - timedelta(days=30)
            end_date = now
        else:
            await callback.answer("❌ Неизвестный период", show_alert=True)
            return
        
        # Сохраняем фильтр в состоянии
        await state.update_data(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Показываем галерею с фильтром
        await gallery_filter_handler.show_gallery_with_date_filter(callback, state, start_date, end_date)
        
    except Exception as e:
        logger.exception(f"Ошибка при фильтрации по дате: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@router.callback_query(GalleryFilterStates.waiting_custom_date)
async def handle_custom_date_input(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает ввод пользовательского периода"""
    try:
        # Получаем текст из сообщения
        text = callback.message.text
        
        # Парсим даты
        try:
            start_str, end_str = text.split("-")
            start_date = datetime.strptime(start_str.strip(), "%d.%m.%Y")
            end_date = datetime.strptime(end_str.strip(), "%d.%m.%Y")
            
            # Проверяем корректность периода
            if end_date < start_date:
                await callback.answer("❌ Конечная дата не может быть раньше начальной", show_alert=True)
                return
            
            # Проверяем, что период не слишком большой
            if (end_date - start_date).days > 90:
                await callback.answer("❌ Период не может быть больше 90 дней", show_alert=True)
                return
            
            # Сохраняем фильтр в состоянии
            await state.update_data(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            
            # Показываем галерею без фильтров
            await gallery_viewer.show_gallery_main(callback, state)
            
        except ValueError:
            await callback.answer("❌ Неверный формат даты", show_alert=True)
            return
        
    except Exception as e:
        logger.exception(f"Ошибка при обработке пользовательского периода: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# ==================== СБРОС ФИЛЬТРОВ ====================

@router.callback_query(F.data == "gallery_reset_filters")
async def handle_reset_filters(callback: CallbackQuery, state: FSMContext):
    """Сбрасывает все фильтры"""
    try:
        # Очищаем фильтры из состояния
        await state.update_data(
            generation_type=None,
            start_date=None,
            end_date=None
        )
        
        # Показываем галерею без фильтров
        from .viewer.main import GalleryViewer
        gallery_viewer = GalleryViewer()
        await gallery_viewer.show_gallery_main(callback, state)
        
        await callback.answer("✅ Фильтры сброшены")
        
    except Exception as e:
        logger.exception(f"Ошибка сброса фильтров: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True) 