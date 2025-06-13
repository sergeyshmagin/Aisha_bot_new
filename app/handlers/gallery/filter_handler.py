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
    
    async def show_gallery_with_type_filter(self, callback: CallbackQuery, state: FSMContext, generation_type: str):
        """Показывает галерею с фильтром по типу"""
        try:
            # Сохраняем фильтр в состоянии
            await state.update_data(generation_type=generation_type)
            
            # Показываем галерею с фильтром
            await self.gallery_viewer.show_gallery_main(callback, state)
            
        except Exception as e:
            logger.exception(f"Ошибка при показе галереи с фильтром {generation_type}: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)
    
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
        
        await callback.message.edit_text(
            "📅 **Фильтр по дате**\n\nВыберите период для просмотра изображений:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def show_filter_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню фильтров"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎭 По типу", callback_data="gallery_filter_type"),
                InlineKeyboardButton(text="📅 По дате", callback_data="gallery_filter_date")
            ],
            [
                InlineKeyboardButton(text="🔄 Сбросить", callback_data="gallery_reset_filters"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="gallery_all")
            ]
        ])
        
        await callback.message.edit_text(
            "🔍 **Фильтры галереи**\n\nВыберите тип фильтрации:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


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
            InlineKeyboardButton(text="◀️ Назад", callback_data="gallery_all")
        ]
    ])
    
    await callback.message.edit_text(
        "Выберите тип изображений:",
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
    """Обрабатывает выбор периода"""
    try:
        # Получаем период из callback_data
        period = callback.data.split(":")[1]
        
        # Вычисляем даты в зависимости от периода
        now = datetime.utcnow()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "yesterday":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "month":
            start_date = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "custom":
            # Переходим в состояние выбора периода
            await state.set_state(GalleryFilterStates.waiting_custom_date)
            await callback.message.edit_text(
                "Введите период в формате:\n"
                "ДД.ММ.ГГГГ-ДД.ММ.ГГГГ\n"
                "Например: 01.06.2025-15.06.2025",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Отмена", callback_data="my_gallery")]
                ])
            )
            return
        else:
            await callback.answer("❌ Неизвестный период", show_alert=True)
            return
        
        # Сохраняем фильтр в состоянии
        await state.update_data(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Показываем галерею без фильтров
        await gallery_viewer.show_gallery_main(callback, state)
        
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
async def reset_filters(callback: CallbackQuery, state: FSMContext):
    """Сбрасывает все фильтры"""
    try:
        # Очищаем состояние фильтров
        await state.update_data(
            generation_type=None,
            start_date=None,
            end_date=None
        )
        
        # Показываем галерею без фильтров
        await gallery_viewer.show_gallery_main(callback, state)
        
    except Exception as e:
        logger.exception(f"Ошибка при сбросе фильтров: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True) 