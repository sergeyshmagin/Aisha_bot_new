"""
Единый сервис отображения промптов
Устраняет дублирование кода между галереей и результатами генерации
"""
import html
from uuid import UUID
from typing import Optional

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger
from app.utils.datetime_utils import format_datetime_for_user

logger = get_logger(__name__)


class PromptDisplayService(BaseHandler):
    """Единый сервис для отображения полных промптов генераций"""
    
    async def show_full_prompt(
        self, 
        callback: CallbackQuery, 
        return_callback: Optional[str] = None
    ):
        """
        Показывает полный промпт генерации
        
        Args:
            callback: Callback query с данными в формате "action:{generation_id}"
            return_callback: Callback для кнопки возврата (по умолчанию "my_gallery")
        """
        try:
            # Извлекаем generation_id из callback_data
            data_parts = callback.data.split(":")
            if len(data_parts) < 2:
                await callback.answer("❌ Неверный формат данных", show_alert=True)
                return
                
            generation_id = UUID(data_parts[1])
            logger.info(f"[PromptDisplay] Показ промпта для generation_id={generation_id}")

            # Получаем пользователя
            user = await self.get_user_from_callback(callback)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            # Получаем генерацию
            generation = await self._get_generation_by_id(generation_id)
            if not generation:
                await callback.answer("❌ Генерация не найдена", show_alert=True)
                return

            # ДЕТАЛЬНОЕ логирование для диагностики
            logger.info(f"[PromptDisplay] Generation user_id: {generation.user_id} (type: {type(generation.user_id)})")
            logger.info(f"[PromptDisplay] Current user.id: {user.id} (type: {type(user.id)})")
            logger.info(f"[PromptDisplay] User telegram_id: {user.telegram_id}")
            
            # Приводим к одному типу для корректного сравнения
            generation_user_id = str(generation.user_id)
            current_user_id = str(user.id)
            
            # Проверяем принадлежность пользователю
            if generation_user_id != current_user_id:
                logger.warning(f"[PromptDisplay] Ownership mismatch: {generation_user_id} != {current_user_id}")
                await callback.answer("❌ Генерация не принадлежит вам", show_alert=True)
                return
            else:
                logger.info(f"[PromptDisplay] Ownership verified: {generation_user_id} == {current_user_id}")

            logger.info(f"[PromptDisplay] Ownership verified for user {user.telegram_id}")

            # Форматируем текст промпта с дополнительной информацией
            date_str = await format_datetime_for_user(generation.created_at, user.id)
            
            # ПРАВИЛЬНО экранируем HTML-символы в промпте
            escaped_prompt = html.escape(generation.final_prompt)
            
            text = f"""📝 <b>Полный промпт генерации</b>

🆔 <b>ID:</b> {str(generation.id)[:8]}...
📅 <b>Дата:</b> {date_str}

<b>Промпт:</b>
<pre>{escaped_prompt}</pre>

📐 <b>Формат:</b> {generation.aspect_ratio}
⚡ <b>Модель:</b> FLUX 1.1 Ultra"""

            # Клавиатура для возврата
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔙 Назад", 
                    callback_data=return_callback or "my_gallery"
                )]
            ])

            # Отправляем с оптимальным форматированием
            await self._send_formatted_prompt(callback, text, keyboard)
            
            logger.info(f"[PromptDisplay] Промпт успешно отправлен для {generation_id}")

        except Exception as e:
            logger.exception(f"[PromptDisplay] Ошибка показа промпта: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def _send_formatted_prompt(
        self, 
        callback: CallbackQuery, 
        text: str, 
        keyboard: InlineKeyboardMarkup
    ):
        """
        Отправляет отформатированный промпт с обработкой разных типов сообщений
        """
        try:
            # Если сообщение с фото - удаляем и отправляем новое
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # Текстовое сообщение - редактируем
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            
        except TelegramBadRequest as e:
            if "parse entities" in str(e):
                logger.warning(f"[PromptDisplay] HTML parsing error, fallback to plain text: {e}")
                
                # Fallback: отправляем без форматирования
                plain_text = text.replace("<b>", "").replace("</b>", "").replace("<pre>", "").replace("</pre>", "")
                
                try:
                    if callback.message.photo:
                        await callback.message.delete()
                        await callback.message.answer(
                            plain_text,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        await callback.message.edit_text(
                            plain_text,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                except Exception as fallback_error:
                    logger.exception(f"[PromptDisplay] Critical error in fallback: {fallback_error}")
                    await callback.answer("❌ Ошибка отображения промпта", show_alert=True)
            else:
                logger.exception(f"[PromptDisplay] Other Telegram error: {e}")
                await callback.answer("❌ Ошибка отображения", show_alert=True)
                
        except Exception as e:
            logger.exception(f"[PromptDisplay] General error sending prompt: {e}")
            await callback.answer("❌ Ошибка отправки промпта", show_alert=True)

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


# Создаем единственный экземпляр для переиспользования
prompt_display_service = PromptDisplayService() 