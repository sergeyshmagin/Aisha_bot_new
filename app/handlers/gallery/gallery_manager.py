"""
Модуль для управления изображениями в галерее
"""
from typing import Optional, Dict, Any
from uuid import UUID

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.core.logger import get_logger
from app.core.di import get_user_service
from app.database.models.generation import ImageGeneration
from app.services.generation.generation_service import ImageGenerationService
from .keyboards import (
    build_delete_confirmation_keyboard, 
    build_gallery_stats_keyboard
)

logger = get_logger(__name__)


class GalleryManager(BaseHandler):
    """Класс для управления изображениями в галерее"""
    
    def __init__(self):
        self.generation_service = ImageGenerationService()
    
    async def show_full_prompt(self, callback: CallbackQuery):
        """Показывает полный промпт генерации"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                return
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Проверяем принадлежность
            if generation.user_id != user.id:
                await callback.answer("❌ Изображение не принадлежит вам", show_alert=True)
                return
            
            # Показываем полный промпт
            text = f"""📝 <b>Полный промпт</b>

🎭 <b>Аватар:</b> {generation.avatar.name if generation.avatar else "Неизвестный"}
📅 <b>Дата:</b> {generation.created_at.strftime('%d.%m.%Y %H:%M')}
📐 <b>Формат:</b> {generation.aspect_ratio}
⚡ <b>Модель:</b> FLUX 1.1 Ultra

<b>Промпт:</b>
<code>{generation.final_prompt}</code>"""
            
            # Клавиатура для возврата
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К галерее",
                        callback_data="my_gallery"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка показа полного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def toggle_favorite(self, callback: CallbackQuery):
        """Переключает статус избранного для изображения"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем пользователя как в старом коде
            user_telegram_id = callback.from_user.id
            from app.core.di import get_user_service
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Приводим оба ID к UUID для корректного сравнения (как в старом коде)
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
            
            # Переключаем статус избранного
            new_favorite_status = await self.generation_service.toggle_favorite(generation_id, user.id)
            
            # Уведомляем пользователя
            status_text = "добавлено в избранное" if new_favorite_status else "удалено из избранного"
            await callback.answer(f"💛 Изображение {status_text}", show_alert=False)
            
            # Возвращаемся к галерее для обновления (просто перезагружаем галерею)
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка переключения избранного: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def request_delete_confirmation(self, callback: CallbackQuery):
        """Запрашивает подтверждение удаления изображения (адаптировано из старого кода)"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = data_parts[1]
            
            # Получаем пользователя как в старом коде
            user_telegram_id = callback.from_user.id
            from app.core.di import get_user_service
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию для отображения информации
            generation = await self.generation_service.get_generation_by_id(UUID(generation_id))
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Приводим оба ID к UUID для корректного сравнения (как в старом коде)
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
            
            # Формируем предварительный просмотр (как в старом коде)
            prompt_preview = generation.final_prompt[:40] + "..." if len(generation.final_prompt) > 40 else generation.final_prompt
            created_str = generation.created_at.strftime("%d.%m.%Y %H:%M")
            
            text = f"""🗑️ *Удаление изображения*

⚠️ *ВНИМАНИЕ!* Вы действительно хотите удалить это изображение?

📝 *Промпт:* {prompt_preview}
🎭 *Аватар:* {generation.avatar.name if generation.avatar else "Неизвестный"}
📅 *Создано:* {created_str}
🆔 *ID:* {str(generation.id)[:8]}

❗ *Это действие необратимо!*"""

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"gallery_delete_confirm:{generation_id}"),
                    InlineKeyboardButton(text="❌ Отмена", callback_data="my_gallery")
                ],
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery")
                ]
            ])
            
            # Безопасная отправка (как в старом коде)
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
            logger.exception(f"Ошибка запроса подтверждения удаления: {e}")
            await callback.answer("❌ Ошибка при удалении", show_alert=True)
    
    async def confirm_delete_image(self, callback: CallbackQuery):
        """Подтверждает и выполняет удаление изображения (адаптировано из старого кода)"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем пользователя как в старом коде
            user_telegram_id = callback.from_user.id
            from app.core.di import get_user_service
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Приводим оба ID к UUID для корректного сравнения (как в старом коде)
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
            
            # Выполняем удаление
            success = await self.generation_service.delete_generation(generation_id)
            
            if success:
                # Очищаем кэш галереи (ВАЖНО для обновления)
                from .gallery_viewer import gallery_cache
                await gallery_cache.clear_user_cache(user.id)
                
                await callback.answer("✅ Изображение удалено", show_alert=True)
                
                # Возвращаемся к галерее (просто перезагружаем)
                from .gallery_viewer import GalleryViewer
                gallery_viewer = GalleryViewer()
                from aiogram.fsm.context import FSMContext
                state = FSMContext(storage=None, key=None)  # Пустое состояние
                await gallery_viewer.show_gallery_main(callback, state, user=user)
                
            else:
                await callback.answer("❌ Не удалось удалить изображение", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка удаления изображения: {e}")
            await callback.answer("❌ Произошла ошибка при удалении", show_alert=True)
    
    async def regenerate_image(self, callback: CallbackQuery):
        """Повторная генерация изображения (адаптировано из старого кода)"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем пользователя как в старом коде
            user_telegram_id = callback.from_user.id
            from app.core.di import get_user_service
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(str(user_telegram_id))
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем оригинальную генерацию
            generation = await self.generation_service.get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Приводим оба ID к UUID для корректного сравнения (как в старом коде)
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
            
            # Создаем новую генерацию с теми же параметрами
            from app.database.models.generation import CreateImageGenerationRequest
            
            request = CreateImageGenerationRequest(
                prompt=generation.final_prompt,
                avatar_id=generation.avatar_id,
                aspect_ratio=generation.aspect_ratio,
                quality_preset=generation.quality_preset
            )
            
            # Запускаем новую генерацию
            new_generation = await self.generation_service.create_generation(
                user_id=user.id,
                request=request
            )
            
            if new_generation:
                await callback.answer("🎨 Запущена повторная генерация!", show_alert=True)
                
                # Перенаправляем пользователя к мониторингу генерации
                from app.handlers.generation.generation_monitor import generation_monitor
                await generation_monitor.show_generation_progress(
                    callback.message, 
                    user, 
                    new_generation.id
                )
            else:
                await callback.answer("❌ Не удалось запустить генерацию", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка повторной генерации: {e}")
            await callback.answer("❌ Произошла ошибка при повторной генерации", show_alert=True)
    
    @require_user()
    async def show_gallery_stats(self, callback: CallbackQuery, user=None):
        """Показывает статистику галереи пользователя (адаптировано из старого кода)"""
        
        try:
            # Получаем детальную статистику
            stats = await self._get_detailed_stats(user.id)
            
            # Формируем текст статистики (как в старом коде)
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

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔙 К галерее", callback_data="my_gallery")
                ]
            ])
            
            # Безопасная отправка статистики (адаптировано из старого кода)
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
            except Exception as edit_error:
                from aiogram.exceptions import TelegramBadRequest
                if isinstance(edit_error, TelegramBadRequest):
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
                    # Общая ошибка - fallback
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode=None
                    )
            
            await callback.answer()
            
        except Exception as e:
            logger.exception(f"Ошибка показа статистики галереи: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке статистики", show_alert=True)
    
    async def _get_detailed_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Получает детальную статистику пользователя (адаптировано из старого кода)"""
        
        try:
            # Получаем все генерации пользователя
            all_generations = await self.generation_service.get_user_generations(
                user_id=user_id,
                limit=1000  # Большой лимит для статистики
            )
            
            from datetime import datetime, timedelta
            from collections import Counter
            
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            
            # Базовая статистика
            total_images = len(all_generations)
            
            # Избранные (предполагаем что есть поле is_favorite)
            favorite_images = len([g for g in all_generations if getattr(g, 'is_favorite', False)])
            
            # За последние 30 дней
            recent_images = len([g for g in all_generations if g.created_at >= thirty_days_ago])
            estimated_credits = recent_images * 5  # Примерная оценка
            
            # Уникальные аватары
            used_avatars = len(set(g.avatar_id for g in all_generations if g.avatar_id))
            
            # Получаем активные аватары напрямую через сессию БД (как в старом коде)
            active_avatars = 0
            try:
                from app.core.database import get_session
                async with get_session() as session:
                    from sqlalchemy import select
                    from app.database.models import Avatar
                    
                    stmt = select(Avatar).where(
                        Avatar.user_id == user_id,
                        Avatar.status == "completed"  # Используем строку вместо enum
                    )
                    result = await session.execute(stmt)
                    active_avatars = len(list(result.scalars().all()))
            except Exception as e:
                logger.warning(f"Ошибка получения активных аватаров: {e}")
            
            # Последняя генерация
            last_generation = "Никогда"
            if all_generations:
                sorted_gens = sorted(all_generations, key=lambda x: x.created_at, reverse=True)
                last_generation = sorted_gens[0].created_at.strftime("%d.%m.%Y %H:%M")
            
            # Наиболее активный период (простая эвристика как в старом коде)
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
            logger.exception(f"Ошибка получения детальной статистики для пользователя {user_id}: {e}")
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