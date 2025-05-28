"""
Роутер для обработки webhook от FAL AI
Интегрирован с основной БД и сервисами бота
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import aiohttp
from uuid import UUID
import sys
import os

# Добавляем путь к основному приложению
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.database.connection import get_async_session
from app.services.avatar.training_service import AvatarTrainingService
from app.services.user import get_user_service_with_session
from app.core.config import settings as main_settings
from ..core.config import settings
from ..core.logger import get_webhook_logger

logger = get_webhook_logger()

router = APIRouter(prefix="/api/v1/avatar", tags=["avatar"])

# Используем реальную сессию БД из основного приложения
async def get_db_session() -> AsyncSession:
    """Получение сессии БД из основного приложения"""
    async for session in get_async_session():
        return session

@router.post("/status_update")
async def handle_fal_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Обработчик webhook от FAL AI для обновления статуса обучения аватаров
    """
    try:
        # Получаем данные webhook
        webhook_data = await request.json()
        
        logger.info(f"[WEBHOOK] Получен webhook от FAL AI: {webhook_data}")
        
        # Извлекаем основную информацию
        request_id = webhook_data.get("request_id")
        status = webhook_data.get("status")
        
        if not request_id:
            logger.error("[WEBHOOK] Отсутствует request_id в webhook")
            raise HTTPException(status_code=400, detail="Missing request_id")
        
        # Определяем тип обучения из query параметров
        training_type = request.query_params.get("training_type", "portrait")
        
        logger.info(f"[WEBHOOK] Обработка статуса '{status}' для request_id: {request_id}, тип: {training_type}")
        
        # Добавляем фоновую задачу для обработки
        background_tasks.add_task(
            process_webhook_background,
            webhook_data,
            training_type
        )
        
        return JSONResponse(
            status_code=200,
            content={"status": "received", "request_id": request_id}
        )
        
    except Exception as e:
        logger.exception(f"[WEBHOOK] Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_webhook_background(
    webhook_data: Dict[str, Any],
    training_type: str
):
    """
    Фоновая обработка webhook от FAL AI с использованием основных сервисов
    """
    try:
        request_id = webhook_data.get("request_id")
        status = webhook_data.get("status")
        
        logger.info(f"[WEBHOOK BACKGROUND] Начинаем обработку {request_id}, статус: {status}")
        
        # Получаем новую сессию для фоновой задачи
        async for session in get_async_session():
            try:
                # Используем основной сервис обучения аватаров
                training_service = AvatarTrainingService(session)
                
                # Обрабатываем webhook через основной сервис
                success = await training_service.handle_webhook(webhook_data)
                
                if success:
                    logger.info(f"[WEBHOOK BACKGROUND] Webhook {request_id} обработан успешно")
                    
                    # Если обучение завершено - отправляем уведомление
                    if status and status.lower() == "completed":
                        await send_completion_notification(webhook_data, session)
                else:
                    logger.warning(f"[WEBHOOK BACKGROUND] Webhook {request_id} не был обработан")
                
                break  # Выходим из цикла после успешной обработки
                
            except Exception as e:
                logger.exception(f"[WEBHOOK BACKGROUND] Ошибка обработки в сессии: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
        
    except Exception as e:
        logger.exception(f"[WEBHOOK BACKGROUND] Критическая ошибка фоновой обработки: {e}")

async def send_completion_notification(
    webhook_data: Dict[str, Any],
    session: AsyncSession
):
    """
    Отправляет уведомление пользователю о завершении обучения
    """
    try:
        request_id = webhook_data.get("request_id")
        
        # Находим аватар по request_id
        training_service = AvatarTrainingService(session)
        avatar = await training_service._find_avatar_by_request_id(request_id)
        
        if not avatar:
            logger.warning(f"[NOTIFICATION] Аватар с request_id {request_id} не найден")
            return
        
        # Получаем пользователя
        user_service = get_user_service_with_session(session)
        user = await user_service.get_user_by_id(avatar.user_id)
        
        if not user or not user.telegram_id:
            logger.warning(f"[NOTIFICATION] Пользователь не найден для аватара {avatar.id}")
            return
        
        # Отправляем уведомление через Telegram
        bot = Bot(token=main_settings.TELEGRAM_TOKEN)
        
        try:
            # Формируем сообщение
            training_type = webhook_data.get("training_type", "portrait")
            if training_type == "portrait":
                emoji = "🎭"
                type_name = "Портретный"
            else:
                emoji = "🎨"
                type_name = "Художественный"
            
            message = (
                f"🎉 **Ваш аватар готов!**\n\n"
                f"{emoji} **{avatar.name}** ({type_name} стиль)\n"
                f"✅ Обучение завершено успешно\n\n"
                f"Теперь вы можете использовать аватар для генерации изображений!\n\n"
                f"Перейдите в меню → Аватары для использования."
            )
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"[NOTIFICATION] Уведомление отправлено пользователю {user.telegram_id}")
            
        finally:
            await bot.session.close()
        
    except Exception as e:
        logger.exception(f"[NOTIFICATION] Ошибка отправки уведомления: {e}")

@router.get("/test_webhook")
async def test_webhook():
    """Тестовый эндпоинт для проверки работы API"""
    return {
        "status": "ok",
        "message": "Webhook API работает",
        "fal_webhook_url": settings.FAL_WEBHOOK_URL,
        "ssl_enabled": settings.SSL_ENABLED,
        "main_settings_webhook": main_settings.FAL_WEBHOOK_URL
    } 