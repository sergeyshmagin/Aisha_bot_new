"""
Утилиты для работы с Telegram API
"""
import logging
import html
from typing import Optional
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from app.core.logger import get_logger

logger = get_logger(__name__)

async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML",
    disable_web_page_preview: Optional[bool] = None
) -> bool:
    """
    Безопасно редактирует текст сообщения с обработкой исключений
    
    Args:
        message: Сообщение для редактирования
        text: Новый текст
        reply_markup: Клавиатура (опционально)
        parse_mode: Режим парсинга (по умолчанию HTML)
        disable_web_page_preview: Отключить превью ссылок
        
    Returns:
        bool: True если сообщение было успешно отредактировано, False если нет изменений
    """
    try:
        await message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
        return True
        
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug("Сообщение не изменилось, редактирование пропущено")
            return False
        else:
            logger.exception(f"Telegram ошибка при редактировании сообщения: {e}")
            raise
    except Exception as e:
        logger.exception(f"Критическая ошибка при редактировании сообщения: {e}")
        raise

async def safe_edit_callback_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = "HTML",
    disable_web_page_preview: Optional[bool] = None,
    answer_callback: bool = True
) -> bool:
    """
    Безопасно редактирует сообщение из callback с обработкой исключений
    
    Args:
        callback: CallbackQuery
        text: Новый текст
        reply_markup: Клавиатура (опционально)
        parse_mode: Режим парсинга (по умолчанию HTML)
        disable_web_page_preview: Отключить превью ссылок
        answer_callback: Отвечать на callback (по умолчанию True)
        
    Returns:
        bool: True если сообщение было успешно отредактировано, False если нет изменений
    """
    try:
        # ✅ ПРОВЕРКА: есть ли текст в сообщении для редактирования
        if not callback.message.text and not callback.message.caption:
            logger.warning("Попытка редактировать сообщение без текста - отправляем новое")
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            if answer_callback:
                await callback.answer()
            return True
        
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview
        )
        
        if answer_callback:
            await callback.answer()
        return True
        
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug("Сообщение не изменилось, редактирование пропущено")
            if answer_callback:
                await callback.answer()
            return False
        elif "query is too old" in str(e):
            logger.warning("Callback слишком старый")
            # Не отвечаем на старый callback
            return False
        elif "there is no text in the message to edit" in str(e):
            logger.warning("Сообщение не содержит текста для редактирования - отправляем новое")
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            if answer_callback:
                await callback.answer()
            return True
        else:
            logger.exception(f"Telegram ошибка при редактировании через callback: {e}")
            if answer_callback:
                try:
                    await callback.answer("❌ Произошла ошибка", show_alert=True)
                except:
                    pass  # Игнорируем ошибки при ответе на callback
            raise
    except Exception as e:
        logger.exception(f"Критическая ошибка при редактировании через callback: {e}")
        if answer_callback:
            try:
                await callback.answer("❌ Произошла ошибка", show_alert=True)
            except:
                pass  # Игнорируем ошибки при ответе на callback
        raise 

def escape_html_for_telegram(text: str) -> str:
    """
    Экранирует HTML-символы для безопасного отображения в Telegram
    
    Args:
        text: Исходный текст
        
    Returns:
        Экранированный текст
    """
    if not text:
        return ""
    return html.escape(text)

def format_prompt_for_display(prompt: str, max_length: int = 80) -> str:
    """
    Форматирует промпт для безопасного отображения в Telegram
    
    Args:
        prompt: Исходный промпт
        max_length: Максимальная длина для отображения
        
    Returns:
        Отформатированный и экранированный промпт
    """
    if not prompt:
        return "Не указан"
    
    escaped_prompt = escape_html_for_telegram(prompt)
    
    if len(escaped_prompt) > max_length:
        return f"{escaped_prompt[:max_length]}..."
    
    return escaped_prompt 