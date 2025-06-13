"""
Статистика галереи изображений
Детальная аналитика пользовательской активности
"""
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from collections import Counter

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.shared.handlers.base_handler import BaseHandler
from app.shared.decorators.auth_decorators import require_user
from app.core.logger import get_logger

logger = get_logger(__name__)


class GalleryStatsManager(BaseHandler):
    """Менеджер статистики галереи"""
    
    @require_user()
    async def show_gallery_stats(self, callback: CallbackQuery, user=None):
        """Показывает статистику галереи пользователя (из LEGACY кода)"""
        
        try:
            # Получаем детальную статистику
            stats = await self._get_detailed_stats(user.id)
            
            # Формируем текст статистики (как в LEGACY коде)
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
            
            # Безопасная отправка статистики (адаптировано из LEGACY кода)
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
        """Получает детальную статистику пользователя (адаптировано из LEGACY кода)"""
        
        try:
            # Получаем все генерации пользователя
            from app.services.generation.generation_service import ImageGenerationService
            generation_service = ImageGenerationService()
            
            all_generations = await generation_service.get_user_generations(
                user_id=user_id,
                limit=1000  # Большой лимит для статистики
            )
            
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
            
            # Получаем активные аватары напрямую через сессию БД (как в LEGACY коде)
            active_avatars = 0
            try:
                from app.core.database import get_session
                from app.database.models import Avatar
                from sqlalchemy import select
                
                async with get_session() as session:
                    # Используем строку напрямую для совместимости с БД
                    stmt = select(Avatar).where(
                        Avatar.user_id == user_id,
                        Avatar.status == 'completed'  # Используем строку вместо enum
                    )
                    result = await session.execute(stmt)
                    avatars = result.scalars().all()
                    active_avatars = len(list(avatars))
            except Exception as e:
                logger.warning(f"Ошибка получения активных аватаров: {e}")
                active_avatars = 0  # Устанавливаем 0 при ошибке
            
            # Последняя генерация
            last_generation = "Никогда"
            if all_generations:
                sorted_gens = sorted(all_generations, key=lambda x: x.created_at, reverse=True)
                last_generation = sorted_gens[0].created_at.strftime("%d.%m.%Y %H:%M")
            
            # Наиболее активный период (простая эвристика как в LEGACY коде)
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