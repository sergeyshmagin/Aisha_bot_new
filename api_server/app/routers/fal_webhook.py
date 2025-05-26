"""
Webhook роутер для обработки уведомлений от FAL AI
Улучшенная версия на основе старой реализации
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import aiohttp

from ..core.config import settings
from ..core.logger import get_webhook_logger

# Импорты из основного проекта
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.database.connection import get_async_session
from app.services.avatar.training_service import AvatarTrainingService
from app.services.user import get_user_service_with_session

router = APIRouter(prefix="/api/v1", tags=["FAL Webhook"])
webhook_logger = get_webhook_logger()

# Глобальный Bot instance
bot_instance: Optional[Bot] = None

async def get_bot() -> Bot:
    """Получает Bot instance для отправки уведомлений"""
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=settings.TELEGRAM_TOKEN)
    return bot_instance

def parse_fal_comment(comment: str) -> Dict[str, str]:
    """
    Парсит комментарий от FAL AI для извлечения метаданных
    Формат: 'user_id=123;avatar_id=abc;training_type=portrait'
    """
    result = {}
    if not comment:
        return result
    
    try:
        for part in comment.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                result[key.strip()] = value.strip()
    except Exception as e:
        webhook_logger.warning(f"Ошибка парсинга комментария '{comment}': {e}")
    
    return result

async def send_avatar_ready_notification(
    user_telegram_id: str, 
    avatar_name: str, 
    training_type: str
) -> bool:
    """
    Отправляет уведомление пользователю о готовности аватара
    """
    try:
        bot = await get_bot()
        
        # Формируем сообщение в зависимости от типа обучения
        if training_type == "portrait":
            emoji = "🎭"
            type_name = "Портретный стиль"
        else:
            emoji = "🎨"
            type_name = "Художественный стиль"
        
        message = (
            f"🎉 **Ваш аватар готов!**\n\n"
            f"{emoji} **{avatar_name}** ({type_name})\n"
            f"✅ Обучение завершено успешно\n\n"
            f"Теперь вы можете использовать аватар для генерации изображений!"
        )
        
        await bot.send_message(
            chat_id=user_telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        webhook_logger.info(f"✅ Уведомление о готовности аватара отправлено пользователю {user_telegram_id}")
        return True
        
    except Exception as e:
        webhook_logger.exception(f"❌ Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")
        return False

@router.post("/avatar/status_update")
async def fal_avatar_status_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Webhook endpoint для получения уведомлений от FAL AI о статусе обучения аватаров
    
    Улучшенная версия старого endpoint с интеграцией в новую систему
    """
    try:
        # Получаем данные webhook
        webhook_data = await request.json()
        
        webhook_logger.info(f"[FAL WEBHOOK] Получен webhook: {webhook_data}")
        
        # Извлекаем базовые поля
        request_id = webhook_data.get("request_id") or webhook_data.get("finetune_id")
        status = webhook_data.get("status")
        comment = webhook_data.get("comment", "")
        
        # Извлекаем user_id и avatar_id из различных источников
        user_id = webhook_data.get("user_id")
        avatar_id = webhook_data.get("avatar_id")
        training_type = webhook_data.get("training_type", "portrait")
        
        # Парсим метаданные из комментария если основные поля отсутствуют
        if (not user_id or not avatar_id) and comment:
            parsed_comment = parse_fal_comment(comment)
            user_id = user_id or parsed_comment.get("user_id")
            avatar_id = avatar_id or parsed_comment.get("avatar_id")
            training_type = training_type or parsed_comment.get("training_type", "portrait")
        
        # Валидация обязательных полей
        if not request_id:
            webhook_logger.error(f"request_id/finetune_id отсутствует в webhook: {webhook_data}")
            raise HTTPException(status_code=400, detail="request_id/finetune_id не найден")
        
        # Запускаем обработку в фоне для быстрого ответа FAL AI
        background_tasks.add_task(
            handle_fal_webhook_processing,
            webhook_data,
            session
        )
        
        # Быстро отвечаем FAL AI
        return JSONResponse(
            content={
                "status": "received",
                "request_id": request_id,
                "message": "Webhook принят к обработке"
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        webhook_logger.exception(f"[FAL WEBHOOK] Критическая ошибка получения webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )

async def handle_fal_webhook_processing(
    webhook_data: Dict[str, Any], 
    session: AsyncSession
) -> bool:
    """
    Фоновая обработка webhook от FAL AI
    """
    try:
        webhook_logger.info(f"[FAL WEBHOOK] Начинаем фоновую обработку: {webhook_data}")
        
        # Создаем сервисы
        training_service = AvatarTrainingService(session)
        user_service = get_user_service_with_session(session)
        
        # Обрабатываем webhook через существующий сервис
        success = await training_service.handle_webhook(webhook_data)
        
        if not success:
            webhook_logger.warning("[FAL WEBHOOK] Webhook не был обработан успешно основным сервисом")
            return False
        
        # Отправляем уведомление пользователю если обучение завершено
        status = webhook_data.get("status")
        if status in ["completed", "ready"]:
            await send_completion_notification(webhook_data, training_service, user_service)
        
        webhook_logger.info("[FAL WEBHOOK] Фоновая обработка завершена успешно")
        return True
        
    except Exception as e:
        webhook_logger.exception(f"[FAL WEBHOOK] Критическая ошибка фоновой обработки: {e}")
        return False

async def send_completion_notification(
    webhook_data: Dict[str, Any],
    training_service: AvatarTrainingService,
    user_service
) -> bool:
    """
    Отправляет уведомление о завершении обучения
    """
    try:
        # Извлекаем информацию
        request_id = webhook_data.get("request_id") or webhook_data.get("finetune_id")
        training_type = webhook_data.get("training_type", "portrait")
        
        if not request_id:
            webhook_logger.warning("[FAL WEBHOOK] Нет request_id для отправки уведомления")
            return False
        
        # Находим аватар по request_id
        avatar = await training_service._find_avatar_by_request_id(request_id)
        
        if not avatar:
            webhook_logger.warning(f"[FAL WEBHOOK] Аватар с request_id {request_id} не найден")
            return False
        
        # Получаем пользователя
        user = await user_service.get_user_by_id(avatar.user_id)
        
        if not user or not user.telegram_id:
            webhook_logger.warning(f"[FAL WEBHOOK] Пользователь не найден для аватара {avatar.id}")
            return False
        
        # Отправляем уведомление
        notification_sent = await send_avatar_ready_notification(
            user_telegram_id=str(user.telegram_id),
            avatar_name=avatar.name,
            training_type=training_type
        )
        
        if notification_sent:
            webhook_logger.info(f"[FAL WEBHOOK] Уведомление отправлено пользователю {user.telegram_id}")
        
        return notification_sent
        
    except Exception as e:
        webhook_logger.exception(f"[FAL WEBHOOK] Ошибка отправки уведомления: {e}")
        return False

# Дополнительные endpoint для мониторинга
@router.get("/health")
async def health_check():
    """Проверка здоровья API сервера"""
    return {
        "status": "healthy",
        "service": "Aisha Bot FAL Webhook API",
        "ssl_enabled": settings.SSL_ENABLED
    }

@router.get("/webhook/status")
async def webhook_status():
    """Статус webhook системы"""
    return {
        "webhook_endpoint": "/api/v1/avatar/status_update",
        "ssl_configured": settings.SSL_ENABLED,
        "telegram_bot_configured": bool(settings.TELEGRAM_TOKEN),
        "fal_api_configured": bool(settings.FAL_API_KEY)
    } 