"""
Обработчик фильтров галереи (адаптировано из старого кода)
"""
from datetime import datetime
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


# Создаем экземпляры новых обработчиков для совместимости
gallery_viewer = GalleryViewer()
gallery_manager = GalleryManager()


class GalleryFilterHandler:
    """Обработчик фильтров галереи (адаптировано из старого кода)"""
    
    async def show_filter_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню фильтров галереи"""
        try:
            text = """🔍 **Фильтры галереи**

Настройте параметры для поиска изображений:

📅 **По времени:**
• За день, неделю, месяц
• Выбрать даты

📐 **По размеру:**
• Квадратные (1:1)
• Портретные (3:4, 9:16)
• Альбомные (4:3, 16:9)

🎭 **По аватару:**
• Конкретный аватар
• Тип обучения"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📅 По времени", callback_data="filter_time"),
                    InlineKeyboardButton(text="📐 По размеру", callback_data="filter_size")
                ],
                [
                    InlineKeyboardButton(text="🎭 По аватару", callback_data="filter_avatar")
                ],
                [
                    InlineKeyboardButton(text="✅ Применить", callback_data="apply_filters"),
                    InlineKeyboardButton(text="🗑️ Сбросить", callback_data="reset_filters")
                ],
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery")
                ]
            ])

            await self._safe_send_message(callback, text, keyboard)
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню фильтров: {e}")
            await callback.answer("❌ Ошибка загрузки фильтров", show_alert=True)

    async def _safe_send_message(self, callback: CallbackQuery, text: str, keyboard: InlineKeyboardMarkup):
        """Безопасная отправка сообщения с fallback (как в старом коде)"""
        try:
            # Уровень 1: Попытка с разметкой
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
                
        except TelegramBadRequest as e:
            logger.warning(f"Ошибка парсинга Markdown: {e}")
            try:
                # Уровень 2: Fallback без разметки
                plain_text = text.replace("*", "").replace("_", "").replace("`", "")
                if callback.message.photo:
                    await callback.message.delete()
                    await callback.message.answer(plain_text, reply_markup=keyboard)
                else:
                    await callback.message.edit_text(plain_text, reply_markup=keyboard)
                    
            except Exception as fallback_error:
                logger.error(f"Критическая ошибка отправки сообщения: {fallback_error}")
                # Уровень 3: Минимальный fallback
                try:
                    await callback.answer("❌ Ошибка отображения. Обновите галерею.")
                except:
                    pass


# Создаем экземпляр обработчика
gallery_filter_handler = GalleryFilterHandler()


@router.callback_query(F.data == "gallery_filters")
async def handle_gallery_filters(callback: CallbackQuery, state: FSMContext):
    """Обработчик главного callback для фильтров"""
    logger.info(f"🔍 Обработка callback gallery_filters от пользователя {callback.from_user.id}")
    await gallery_filter_handler.show_filter_menu(callback, state)


@router.callback_query(F.data == "filter_time")
async def handle_filter_time(callback: CallbackQuery, state: FSMContext):
    """Обработчик фильтра по времени"""
    text = """📅 **Фильтр по времени**

Выберите временной период:"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="За день", callback_data="time_day"),
            InlineKeyboardButton(text="За неделю", callback_data="time_week")
        ],
        [
            InlineKeyboardButton(text="За месяц", callback_data="time_month"),
            InlineKeyboardButton(text="За все время", callback_data="time_all")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="gallery_filters")
        ]
    ])

    await gallery_filter_handler._safe_send_message(callback, text, keyboard)


@router.callback_query(F.data == "filter_size")
async def handle_filter_size(callback: CallbackQuery, state: FSMContext):
    """Обработчик фильтра по размеру"""
    text = """📐 **Фильтр по размеру**

Выберите соотношение сторон:"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬛ Квадрат 1:1", callback_data="size_1_1")
        ],
        [
            InlineKeyboardButton(text="📱 Портрет 3:4", callback_data="size_3_4"),
            InlineKeyboardButton(text="📱 Портрет 9:16", callback_data="size_9_16")
        ],
        [
            InlineKeyboardButton(text="🖼️ Альбом 4:3", callback_data="size_4_3"),
            InlineKeyboardButton(text="🖼️ Альбом 16:9", callback_data="size_16_9")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="gallery_filters")
        ]
    ])

    await gallery_filter_handler._safe_send_message(callback, text, keyboard)


@router.callback_query(F.data == "filter_avatar")
async def handle_filter_avatar(callback: CallbackQuery, state: FSMContext):
    """Обработчик фильтра по аватару"""
    await callback.answer("🚧 Фильтр по аватарам в разработке", show_alert=True)


# Заглушки для конкретных значений фильтров
@router.callback_query(F.data.startswith("time_"))
async def handle_time_filter_value(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора конкретного времени"""
    value = callback.data.replace("time_", "")
    await callback.answer(f"🚧 Фильтр '{value}' в разработке", show_alert=True)


@router.callback_query(F.data.startswith("size_"))
async def handle_size_filter_value(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора конкретного размера"""
    value = callback.data.replace("size_", "").replace("_", ":")
    await callback.answer(f"🚧 Фильтр размера '{value}' в разработке", show_alert=True)


@router.callback_query(F.data == "apply_filters")
async def apply_filters(callback: CallbackQuery, state: FSMContext):
    """Применить фильтры (заглушка)"""
    await callback.answer("🚧 Применение фильтров в разработке", show_alert=True)


@router.callback_query(F.data == "reset_filters")
async def reset_filters(callback: CallbackQuery, state: FSMContext):
    """Сбросить фильтры"""
    await callback.answer("🗑️ Фильтры сброшены", show_alert=True)
    # Возвращаемся к галерее
    await handle_gallery_filters(callback, state) 