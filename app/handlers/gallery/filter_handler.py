"""
Оптимизированный обработчик фильтров галереи
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
from app.handlers.gallery.main_handler import show_gallery_image, _safe_send_message

logger = get_logger(__name__)

router = Router()


class GalleryFilterHandler:
    """Обработчик фильтров галереи"""
    
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

            await _safe_send_message(callback, text, keyboard)
            await state.set_state(GalleryFilterStates.selecting_filters)
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню фильтров: {e}")
            await callback.answer("❌ Ошибка загрузки фильтров", show_alert=True)


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

    await _safe_send_message(callback, text, keyboard)


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

    await _safe_send_message(callback, text, keyboard)


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
    """
    Применить фильтры с оптимизацией
    """
    try:
        start_time = datetime.utcnow()
        user_id = UUID(str(callback.from_user.id))
        
        # ✅ 1. Получаем текущие фильтры
        data = await state.get_data()
        filter_data = data.get("filter_data", GalleryFilterData())
        
        # ✅ 2. Формируем словарь фильтров
        filters = {}
        
        if filter_data.time_filter:
            filters["time_filter"] = filter_data.time_filter
            
        if filter_data.size_filters:
            filters["size_filters"] = filter_data.size_filters
            
        if filter_data.avatar_filters:
            filters["avatar_filters"] = filter_data.avatar_filters
        
        # ✅ 3. Получаем отфильтрованные изображения через оптимизированный сервис
        images_data, total_count, has_more = await gallery_service.get_user_images_optimized(
            user_id=user_id,
            filters=filters,
            page=1,
            per_page=100,
            force_refresh=True  # Принудительно обновляем кеш для новых фильтров
        )
        
        if not images_data:
            text = "🔍 *Фильтры применены*\n\n"
            text += "❌ По заданным критериям изображения не найдены.\n\n"
            text += "Попробуйте изменить параметры фильтрации."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔧 Изменить фильтры", callback_data="gallery_filters")],
                [InlineKeyboardButton(text="🗑️ Сбросить фильтры", callback_data="reset_filters")],
                [InlineKeyboardButton(text="🔙 Галерея", callback_data="gallery")]
            ])
            
            await _safe_send_message(callback, text, keyboard)
            await state.clear()
            return
        
        # ✅ 4. Сохраняем результаты фильтрации в кеше
        gallery_cache_key = f"filtered_gallery_{user_id}_{int(datetime.utcnow().timestamp())}"
        gallery_data = GalleryData(
            image_ids=[img["id"] for img in images_data],
            current_index=0,
            total_count=total_count,
            user_id=str(user_id),
            filters=filters
        )
        await gallery_state_manager.set_gallery_data(gallery_cache_key, gallery_data)
        
        # ✅ 5. Показываем первое отфильтрованное изображение
        await show_gallery_image(callback, 0, gallery_cache_key)
        
        # ✅ 6. Очищаем состояние фильтра
        await state.clear()
        
        # ✅ 7. Логируем производительность
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        logger.info(f"🔍 Фильтры применены за {duration:.0f}ms. Найдено {total_count} изображений")
        
    except Exception as e:
        logger.error(f"Ошибка применения фильтров: {e}")
        await callback.answer("❌ Ошибка применения фильтров")


@router.callback_query(F.data == "reset_filters")
async def reset_filters(callback: CallbackQuery, state: FSMContext):
    """
    Сбросить фильтры и показать все изображения
    """
    try:
        start_time = datetime.utcnow()
        user_id = UUID(str(callback.from_user.id))
        
        # ✅ 1. Получаем все изображения без фильтров
        images_data, total_count, has_more = await gallery_service.get_user_images_optimized(
            user_id=user_id,
            filters=None,
            page=1,
            per_page=100,
            force_refresh=False
        )
        
        if not images_data:
            text = "📷 *Ваша галерея пуста*\n\nСоздайте первое изображение!"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎨 Создать изображение", callback_data="generate_image")],
                [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
            ])
            
            await _safe_send_message(callback, text, keyboard)
            await state.clear()
            return
        
        # ✅ 2. Сохраняем данные без фильтров
        gallery_cache_key = f"gallery_{user_id}_{int(datetime.utcnow().timestamp())}"
        gallery_data = GalleryData(
            image_ids=[img["id"] for img in images_data],
            current_index=0,
            total_count=total_count,
            user_id=str(user_id),
            filters={}
        )
        await gallery_state_manager.set_gallery_data(gallery_cache_key, gallery_data)
        
        # ✅ 3. Показываем первое изображение
        await show_gallery_image(callback, 0, gallery_cache_key)
        
        # ✅ 4. Очищаем состояние
        await state.clear()
        
        # ✅ 5. Логируем производительность
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds() * 1000
        logger.info(f"🗑️ Фильтры сброшены за {duration:.0f}ms. Показано {total_count} изображений")
        
    except Exception as e:
        logger.error(f"Ошибка сброса фильтров: {e}")
        await callback.answer("❌ Ошибка сброса фильтров") 