"""
Главный обработчик галереи изображений
Рефакторен - использует новые модули для разделения ответственности
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from uuid import UUID

from app.core.logger import get_logger
from .gallery_viewer import GalleryViewer
from .gallery_manager import GalleryManager
from .keyboards import build_search_keyboard
from app.database.models import ImageGeneration

logger = get_logger(__name__)
router = Router()


class GalleryMainHandler:
    """Главный обработчик галереи изображений"""
    
    def __init__(self):
        self.gallery_viewer = GalleryViewer()
        self.gallery_manager = GalleryManager()


# Создаем экземпляр обработчика
gallery_handler = GalleryMainHandler()

# ==================== ОСНОВНЫЕ РОУТЫ ====================

@router.callback_query(F.data == "my_gallery")
async def handle_gallery_main(callback: CallbackQuery, state: FSMContext):
    """Обработчик главной страницы галереи"""
    gallery_viewer = GalleryViewer()
    await gallery_viewer.show_gallery_main(callback, state)

@router.callback_query(F.data == "gallery_all")
async def handle_gallery_all(callback: CallbackQuery, state: FSMContext):
    """Обработчик показа всех изображений в галерее"""
    logger.info(f"🖼️ Обработка callback gallery_all от пользователя {callback.from_user.id}")
    gallery_viewer = GalleryViewer()
    await gallery_viewer.show_gallery_main(callback, state)

@router.callback_query(F.data.startswith("my_gallery_return:"))
async def handle_gallery_return(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата к галерее с восстановлением позиции"""
    try:
        # Извлекаем generation_id из callback_data
        data_parts = callback.data.split(":")
        generation_id = UUID(data_parts[1])
        
        # Получаем пользователя
        gallery_viewer = GalleryViewer()
        user = await gallery_viewer.get_user_from_callback(callback)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Получаем изображения пользователя
        images = await gallery_viewer._get_user_completed_images(user.id)
        
        if not images:
            await gallery_viewer._show_empty_gallery_message(callback)
            return
        
        # Ищем индекс нужного изображения
        target_index = 0
        for i, img in enumerate(images):
            if img.id == generation_id:
                target_index = i
                break
        
        logger.info(f"Возврат к галерее: пользователь {user.telegram_id}, изображение {generation_id}, индекс {target_index}")
        
        # Показываем галерею с нужным индексом
        await gallery_viewer.show_gallery_main(callback, state, user=user, start_index=target_index)
        
    except Exception as e:
        logger.exception(f"Ошибка возврата к галерее: {e}")
        # Fallback на обычную галерею
        await handle_gallery_main(callback, state)

@router.callback_query(F.data.startswith("gallery_image_prev:"))
async def handle_gallery_prev(callback: CallbackQuery):
    """Обработчик перехода к предыдущему изображению"""
    gallery_viewer = GalleryViewer()
    await gallery_viewer.handle_image_navigation(callback, "prev")

@router.callback_query(F.data.startswith("gallery_image_next:"))
async def handle_gallery_next(callback: CallbackQuery):
    """Обработчик перехода к следующему изображению"""
    gallery_viewer = GalleryViewer()
    await gallery_viewer.handle_image_navigation(callback, "next")

# ==================== УПРАВЛЕНИЕ ИЗОБРАЖЕНИЯМИ ====================

@router.callback_query(F.data.startswith("gallery_full_prompt:"))
async def handle_gallery_full_prompt(callback: CallbackQuery):
    """Обработчик показа полного промпта"""
    from app.utils.prompt_display import prompt_display_service
    await prompt_display_service.show_full_prompt(callback, return_callback="my_gallery")

@router.callback_query(F.data.startswith("gallery_toggle_favorite:"))
async def handle_gallery_toggle_favorite(callback: CallbackQuery):
    """Обработчик переключения избранного"""
    gallery_manager = GalleryManager()
    await gallery_manager.toggle_favorite(callback)

@router.callback_query(F.data.startswith("gallery_favorite:"))
async def handle_gallery_favorite(callback: CallbackQuery):
    """Обработчик избранного (новый callback)"""
    gallery_manager = GalleryManager()
    await gallery_manager.toggle_favorite(callback)

@router.callback_query(F.data.startswith("gallery_delete:"))
async def handle_gallery_delete(callback: CallbackQuery):
    """Обработчик запроса удаления изображения"""
    gallery_manager = GalleryManager()
    await gallery_manager.request_delete_confirmation(callback)

@router.callback_query(F.data.startswith("gallery_delete_confirm:"))
async def handle_gallery_delete_confirm(callback: CallbackQuery):
    """Обработчик подтверждения удаления изображения"""
    gallery_manager = GalleryManager()
    await gallery_manager.deletion_manager.delete_image(callback)

@router.callback_query(F.data.startswith("gallery_regenerate:"))
async def handle_gallery_regenerate(callback: CallbackQuery):
    """Обработчик повторной генерации"""
    gallery_manager = GalleryManager()
    await gallery_manager.regenerate_image(callback)

# ==================== СТАТИСТИКА ====================

@router.callback_query(F.data == "gallery_stats")
async def handle_gallery_stats(callback: CallbackQuery):
    """Обработчик статистики галереи"""
    logger.info(f"📊 Обработка callback gallery_stats от пользователя {callback.from_user.id}")
    
    # Используем реальный менеджер статистики
    from .management.stats import GalleryStatsManager
    stats_manager = GalleryStatsManager()
    await stats_manager.show_gallery_stats(callback)

# ==================== ПОИСК И ФИЛЬТРЫ ====================

@router.callback_query(F.data == "gallery_search")
async def handle_gallery_search(callback: CallbackQuery, state: FSMContext):
    """Обработчик поиска в галерее"""
    
    text = """🔍 <b>Поиск в галерее</b>

📂 <b>Доступные фильтры:</b>

• 📅 <b>По дате</b> - найти изображения за определенный период
• 🎭 <b>По аватару</b> - показать изображения конкретного аватара  
• 📝 <b>По промпту</b> - поиск по тексту промпта
• 💛 <b>Избранные</b> - только избранные изображения

💡 <b>Выберите тип поиска:</b>"""
    
    keyboard = build_search_keyboard()
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ==================== ЗАГЛУШКИ ДЛЯ ФИЛЬТРОВ ====================

@router.callback_query(F.data == "gallery_filters")
async def handle_gallery_filters(callback: CallbackQuery, state: FSMContext):
    """Обработчик фильтров галереи"""
    logger.info(f"🔍 Обработка callback gallery_filters от пользователя {callback.from_user.id}")
    from .filter_handler import gallery_filter_handler
    await gallery_filter_handler.show_filter_menu(callback, state)

@router.callback_query(F.data == "gallery_filter_date")
async def handle_filter_date(callback: CallbackQuery):
    """Фильтр по дате - в разработке"""
    await callback.answer("🚧 Фильтр по дате в разработке", show_alert=True)

@router.callback_query(F.data == "gallery_filter_avatar")
async def handle_filter_avatar(callback: CallbackQuery):
    """Фильтр по аватару - в разработке"""
    await callback.answer("🚧 Фильтр по аватару в разработке", show_alert=True)

@router.callback_query(F.data == "gallery_filter_prompt")
async def handle_filter_prompt(callback: CallbackQuery):
    """Фильтр по промпту - в разработке"""
    await callback.answer("🚧 Поиск по промпту в разработке", show_alert=True)

@router.callback_query(F.data == "gallery_filter_favorites")
async def handle_filter_favorites(callback: CallbackQuery):
    """Фильтр избранных - в разработке"""
    await callback.answer("🚧 Фильтр избранных в разработке", show_alert=True)

# ==================== ВСПОМОГАТЕЛЬНЫЕ РОУТЫ ====================

@router.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    """Обработчик пустых callback'ов"""
    await callback.answer()

@router.callback_query(F.data == "gallery_main")
async def handle_gallery_main_new(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback gallery_main (альтернативный к my_gallery)"""
    logger.info(f"🖼️ Обработка callback gallery_main от пользователя {callback.from_user.id}")
    # Используем тот же обработчик что и для my_gallery
    await handle_gallery_main(callback, state)

@router.callback_query(F.data.startswith("generation_status:"))
async def handle_generation_status(callback: CallbackQuery):
    """Обработчик проверки статуса генерации"""
    try:
        # Извлекаем generation_id из callback_data
        generation_id = callback.data.split(":")[1]
        logger.info(f"📊 Проверка статуса генерации {generation_id}")
        
        # Получаем пользователя
        from app.shared.handlers.base_handler import BaseHandler
        base_handler = BaseHandler()
        user = await base_handler.get_user_from_callback(callback, show_error=False)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Получаем генерацию из БД
        from uuid import UUID
        from app.core.database import get_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with get_session() as session:
            stmt = (
                select(ImageGeneration)
                .options(selectinload(ImageGeneration.avatar))
                .where(
                    ImageGeneration.id == UUID(generation_id),
                    ImageGeneration.user_id == user.id
                )
            )
            result = await session.execute(stmt)
            generation = result.scalar_one_or_none()
        
        if not generation:
            await callback.answer("❌ Генерация не найдена", show_alert=True)
            return
        
        # Формируем ответ в зависимости от статуса
        status_map = {
            'pending': '⏳ В очереди',
            'processing': '🎨 Генерируется...',
            'completed': '✅ Завершена',
            'failed': '❌ Ошибка',
            'cancelled': '⏹️ Отменена'
        }
        
        status_text = status_map.get(generation.status, generation.status)
        
        if generation.status == 'completed':
            # Если генерация завершена - переходим в галерею к этому изображению
            await callback.answer("✅ Генерация завершена! Переходим к изображению...")
            
            # Используем callback для возврата к конкретному изображению
            from aiogram.types import CallbackQuery as NewCallbackQuery
            
            # Создаем новый callback для возврата к галерее
            new_callback_data = f"my_gallery_return:{generation_id}"
            new_callback = NewCallbackQuery(
                id=callback.id,
                from_user=callback.from_user,
                chat_instance=callback.chat_instance,
                message=callback.message,
                data=new_callback_data
            )
            
            # Переходим к галерее с нужным изображением
            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.memory import MemoryStorage
            storage = MemoryStorage()
            state = FSMContext(storage=storage, key=f"user:{user.id}")
            
            await handle_gallery_return(new_callback, state)
            
        else:
            # Показываем текущий статус
            await callback.answer(f"📊 Статус: {status_text}", show_alert=True)
        
    except Exception as e:
        logger.exception(f"Ошибка проверки статуса генерации: {e}")
        await callback.answer("❌ Ошибка проверки статуса", show_alert=True)

@router.callback_query(F.data == "show_current_image")
async def handle_show_current_image(callback: CallbackQuery):
    """Обработчик кнопки 'Показать изображение' при fallback"""
    try:
        # Принудительно обновляем текущее изображение
        gallery_viewer = GalleryViewer()
        
        # Получаем пользователя
        user = await gallery_viewer.get_user_from_callback(callback, show_error=False)
        if not user:
            await callback.answer("❌ Перезайдите в галерею", show_alert=True)
            return
        
        # Получаем изображения из кэша или БД
        from .gallery_viewer import ultra_gallery_cache
        images = await ultra_gallery_cache.get_user_images(user.id)
        if not images:
            images = await gallery_viewer._get_user_completed_images_ultra_fast(user.id)
            if not images:
                await callback.answer("❌ Изображения не найдены", show_alert=True)
                return
        
        # Берем первое изображение или восстанавливаем состояние
        current_idx = 0
        try:
            saved_index = await ultra_gallery_cache.get_user_gallery_state(user.id)
            if saved_index is not None and saved_index < len(images):
                current_idx = saved_index
        except:
            pass
        
        # Принудительно обновляем изображение
        await gallery_viewer._send_image_card_ultra_ultra_fast(callback, images, current_idx, user.id)
        
        logger.info(f"🔄 Принудительное обновление изображения для пользователя {user.telegram_id}")
        
    except Exception as e:
        logger.exception(f"Ошибка принудительного показа изображения: {e}")
        await callback.answer("❌ Ошибка загрузки изображения", show_alert=True)