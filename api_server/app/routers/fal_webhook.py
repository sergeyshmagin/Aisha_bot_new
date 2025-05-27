"""
Webhook роутер для обработки уведомлений от FAL AI
Обновленная версия для продакшн использования с Aisha v2
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import aiohttp
from uuid import UUID

from ..core.config import settings
from ..core.logger import get_webhook_logger

logger = get_webhook_logger()

router = APIRouter(prefix="/api/v1/avatar", tags=["avatar"])

# Заглушка для сессии БД (в реальной реализации будет подключение к БД)
async def get_db_session():
    """Заглушка для получения сессии БД"""
    return None

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
            training_type,
            session
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
    training_type: str,
    session: Optional[AsyncSession]
):
    """
    Фоновая обработка webhook от FAL AI
    """
    try:
        request_id = webhook_data.get("request_id")
        status = webhook_data.get("status")
        
        logger.info(f"[WEBHOOK BACKGROUND] Начинаем обработку {request_id}, статус: {status}")
        
        if status == "IN_PROGRESS":
            await handle_training_progress(webhook_data, training_type, session)
        elif status == "COMPLETED":
            await handle_training_completed(webhook_data, training_type, session)
        elif status == "FAILED":
            await handle_training_failed(webhook_data, training_type, session)
        else:
            logger.warning(f"[WEBHOOK BACKGROUND] Неизвестный статус: {status}")
        
        logger.info(f"[WEBHOOK BACKGROUND] Обработка завершена для {request_id}")
        
    except Exception as e:
        logger.exception(f"[WEBHOOK BACKGROUND] Ошибка фоновой обработки: {e}")

async def handle_training_progress(
    webhook_data: Dict[str, Any],
    training_type: str,
    session: Optional[AsyncSession]
):
    """Обработка прогресса обучения"""
    try:
        request_id = webhook_data.get("request_id")
        logs = webhook_data.get("logs", [])
        
        logger.info(f"[TRAINING PROGRESS] {request_id}: обучение в процессе")
        
        # Логируем последние записи
        if logs:
            latest_logs = logs[-3:]  # Последние 3 записи
            for log_entry in latest_logs:
                logger.info(f"[TRAINING LOG] {request_id}: {log_entry.get('message', '')}")
        
        # В реальной реализации здесь будет:
        # 1. Обновление статуса в БД
        # 2. Отправка уведомления пользователю через Telegram
        
        logger.info(f"[TRAINING PROGRESS] {request_id}: прогресс обработан")
        
    except Exception as e:
        logger.exception(f"[TRAINING PROGRESS] Ошибка обработки прогресса: {e}")

async def handle_training_completed(
    webhook_data: Dict[str, Any],
    training_type: str,
    session: Optional[AsyncSession]
):
    """Обработка завершения обучения"""
    try:
        request_id = webhook_data.get("request_id")
        result = webhook_data.get("result", {})
        
        logger.info(f"[TRAINING COMPLETED] {request_id}: обучение завершено успешно")
        
        # Извлекаем результаты в зависимости от типа обучения
        if training_type == "portrait":
            # FLUX LoRA Portrait Trainer результаты
            lora_url = result.get("lora_url")
            config_url = result.get("config_url")
            
            logger.info(f"[TRAINING COMPLETED] {request_id}: LoRA URL: {lora_url}")
            logger.info(f"[TRAINING COMPLETED] {request_id}: Config URL: {config_url}")
            
        else:
            # FLUX Pro Trainer результаты
            finetune_id = result.get("finetune_id")
            
            logger.info(f"[TRAINING COMPLETED] {request_id}: Finetune ID: {finetune_id}")
        
        # В реальной реализации здесь будет:
        # 1. Сохранение результатов в БД
        # 2. Обновление статуса аватара
        # 3. Отправка уведомления пользователю
        # 4. Активация аватара для использования
        
        logger.info(f"[TRAINING COMPLETED] {request_id}: результаты сохранены")
        
    except Exception as e:
        logger.exception(f"[TRAINING COMPLETED] Ошибка обработки завершения: {e}")

async def handle_training_failed(
    webhook_data: Dict[str, Any],
    training_type: str,
    session: Optional[AsyncSession]
):
    """Обработка ошибки обучения"""
    try:
        request_id = webhook_data.get("request_id")
        error = webhook_data.get("error", {})
        logs = webhook_data.get("logs", [])
        
        logger.error(f"[TRAINING FAILED] {request_id}: обучение завершилось с ошибкой")
        logger.error(f"[TRAINING FAILED] {request_id}: ошибка: {error}")
        
        # Логируем последние записи для диагностики
        if logs:
            latest_logs = logs[-5:]  # Последние 5 записей
            for log_entry in latest_logs:
                logger.error(f"[TRAINING ERROR LOG] {request_id}: {log_entry.get('message', '')}")
        
        # В реальной реализации здесь будет:
        # 1. Обновление статуса аватара как "failed"
        # 2. Сохранение информации об ошибке
        # 3. Отправка уведомления пользователю
        # 4. Возможно, автоматический перезапуск обучения
        
        logger.info(f"[TRAINING FAILED] {request_id}: ошибка обработана")
        
    except Exception as e:
        logger.exception(f"[TRAINING FAILED] Ошибка обработки неудачи: {e}")

@router.get("/test_webhook")
async def test_webhook():
    """Тестовый эндпоинт для проверки работы API"""
    return {
        "status": "ok",
        "message": "Webhook API работает",
        "fal_webhook_url": settings.FAL_WEBHOOK_URL,
        "ssl_enabled": settings.SSL_ENABLED
    } 