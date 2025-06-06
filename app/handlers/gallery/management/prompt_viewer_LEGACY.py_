"""
Просмотр полных промптов изображений
Отображение детальной информации о генерации
"""
from uuid import UUID

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger

logger = get_logger(__name__)


class PromptViewer(BaseHandler):
    """Просмотрщик полных промптов"""
    
    async def show_full_prompt(self, callback: CallbackQuery):
        """Показывает полный промпт генерации (из LEGACY кода)"""
        
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            generation_id = UUID(data_parts[1])
            
            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                return
            
            # Получаем генерацию
            generation = await self._get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Изображение не найдено", show_alert=True)
                return
            
            # Детальное логирование для диагностики
            logger.info(f"[Prompt Viewer] Generation ID: {generation_id}")
            logger.info(f"[Prompt Viewer] Generation user_id: {generation.user_id} (type: {type(generation.user_id)})")
            logger.info(f"[Prompt Viewer] Current user.id: {user.id} (type: {type(user.id)})")
            logger.info(f"[Prompt Viewer] User telegram_id: {user.telegram_id}")
            
            # Проверяем принадлежность с приведением типов
            generation_user_id = str(generation.user_id)
            current_user_id = str(user.id)
            
            if generation_user_id != current_user_id:
                logger.warning(f"[Prompt Viewer] Ownership mismatch: {generation_user_id} != {current_user_id}")
                await callback.answer("❌ Изображение не принадлежит вам", show_alert=True)
                return
            else:
                logger.info(f"[Prompt Viewer] Ownership verified: {generation_user_id} == {current_user_id}")
            
            # Показываем полный промпт как в LEGACY коде
            # Сначала пробуем блок кода с markdown
            prompt_text = f"""```
{generation.final_prompt}
```"""

            # Клавиатура для возврата
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 К галерее",
                        callback_data="my_gallery"
                    )
                ]
            ])
            
            # Правильная обработка сообщений с изображениями
            try:
                if callback.message.photo:
                    # Если это сообщение с фото - удаляем и отправляем новое
                    await callback.message.delete()
                    await callback.message.answer(
                        prompt_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    # Если это текстовое сообщение - редактируем
                    await callback.message.edit_text(
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
                        if callback.message.photo:
                            await callback.message.delete()
                            await callback.message.answer(
                                html_text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                        else:
                            await callback.message.edit_text(
                                html_text,
                                reply_markup=keyboard,
                                parse_mode="HTML"
                            )
                        logger.info(f"✅ Промпт отправлен с HTML для генерации {generation_id}")
                    except Exception as html_error:
                        # Уровень 3: Без форматирования
                        logger.exception(f"Ошибка и с HTML, отправляю без форматирования: {html_error}")
                        
                        try:
                            if callback.message.photo:
                                await callback.message.delete()
                                await callback.message.answer(
                                    generation.final_prompt,
                                    reply_markup=keyboard,
                                    parse_mode=None
                                )
                            else:
                                await callback.message.edit_text(
                                    generation.final_prompt,
                                    reply_markup=keyboard,
                                    parse_mode=None
                                )
                            logger.info(f"✅ Промпт отправлен без форматирования для генерации {generation_id}")
                        except Exception as final_error:
                            logger.exception(f"Критическая ошибка отправки промпта: {final_error}")
                            await callback.answer("❌ Ошибка отображения промпта", show_alert=True)
                            return
                else:
                    # Другая ошибка Telegram
                    logger.exception(f"Другая ошибка Telegram при показе промпта: {markdown_error}")
                    await callback.answer("❌ Ошибка отображения промпта", show_alert=True)
                    return
            except Exception as msg_error:
                # Fallback: всегда удаляем и отправляем новое
                logger.exception(f"Общая ошибка отправки промпта: {msg_error}")
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                    
                await callback.message.answer(
                    prompt_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            
        except Exception as e:
            logger.exception(f"Ошибка показа полного промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _get_generation_by_id(self, generation_id: UUID):
        """Получает генерацию по ID с загрузкой связанных объектов"""
        
        from app.core.database import get_session
        from app.database.models.generation import ImageGeneration
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with get_session() as session:
            stmt = (
                select(ImageGeneration)
                .options(selectinload(ImageGeneration.avatar))
                .where(ImageGeneration.id == generation_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() 