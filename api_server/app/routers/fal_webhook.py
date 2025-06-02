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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ИСПРАВЛЕНИЕ: Добавляем правильные пути для production
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Проверяем что можем импортировать основные модули
try:
    # ИСПРАВЛЕНИЕ: Используем существующий app/core/database.py
    from app.core.database import get_session  # Используем get_session вместо get_async_session
    from app.services.avatar.training_service import AvatarTrainingService
    from app.core.di import get_user_service_with_session  # ИСПРАВЛЕНИЕ: Правильный импорт
    from app.core.config import settings as main_settings
except ImportError as e:
    print(f"❌ Ошибка импорта основных модулей: {e}")
    print(f"🔧 Project root: {project_root}")
    print(f"🔧 Python path: {sys.path}")
    raise

from ..core.config import settings
from ..core.logger import get_webhook_logger

logger = get_webhook_logger()

router = APIRouter(prefix="/api/v1/avatar", tags=["avatar"])

# Используем реальную сессию БД из основного приложения
async def get_db_session() -> AsyncSession:
    """Получение сессии БД из основного приложения"""
    async with get_session() as session:
        yield session

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
    ИСПРАВЛЕНО: Правильная работа с сессией БД и обработка ошибок
    """
    request_id = webhook_data.get("request_id")
    status = webhook_data.get("status")
    
    logger.info(f"[WEBHOOK BACKGROUND] Начинаем обработку {request_id}, статус: {status}")
    logger.info(f"[WEBHOOK BACKGROUND] Данные webhook: {webhook_data}")
    logger.info(f"[WEBHOOK BACKGROUND] Тип обучения: {training_type}")
    
    try:
        # ИСПРАВЛЕНИЕ: Используем правильный async context manager
        logger.info(f"[WEBHOOK BACKGROUND] Создаем сессию БД...")
        
        async with get_session() as session:
            try:
                logger.info(f"[WEBHOOK BACKGROUND] Сессия БД создана успешно")
                
                # Используем основной сервис обучения аватаров
                training_service = AvatarTrainingService(session)
                logger.info(f"[WEBHOOK BACKGROUND] Сервис обучения создан")
                
                # Проверяем что аватар существует
                avatar = await training_service._find_avatar_by_request_id(request_id)
                if not avatar:
                    logger.error(f"[WEBHOOK BACKGROUND] Аватар с request_id {request_id} НЕ найден!")
                    return
                
                logger.info(f"[WEBHOOK BACKGROUND] Найден аватар: {avatar.name} (ID: {avatar.id})")
                logger.info(f"[WEBHOOK BACKGROUND] Текущий статус аватара: {avatar.status}")
                
                # Обрабатываем webhook через основной сервис
                logger.info(f"[WEBHOOK BACKGROUND] Вызываем handle_webhook...")
                success = await training_service.handle_webhook(webhook_data)
                
                if success:
                    logger.info(f"[WEBHOOK BACKGROUND] ✅ Webhook {request_id} обработан успешно")
                    
                    # Проверяем обновился ли аватар
                    await session.refresh(avatar)
                    logger.info(f"[WEBHOOK BACKGROUND] Новый статус аватара: {avatar.status}")
                    logger.info(f"[WEBHOOK BACKGROUND] Finetune ID: {avatar.finetune_id}")
                    
                    # Если обучение завершено - отправляем уведомление
                    if status and status.lower() == "completed":
                        logger.info(f"[WEBHOOK BACKGROUND] Отправляем уведомление о завершении...")
                        await send_completion_notification(webhook_data, session, training_type)
                else:
                    logger.error(f"[WEBHOOK BACKGROUND] ❌ Webhook {request_id} НЕ был обработан")
                
            except Exception as e:
                logger.exception(f"[WEBHOOK BACKGROUND] Ошибка в сессии: {e}")
                await session.rollback()
                raise
        
    except Exception as e:
        logger.exception(f"[WEBHOOK BACKGROUND] Критическая ошибка фоновой обработки: {e}")

async def send_completion_notification(
    webhook_data: Dict[str, Any],
    session: AsyncSession,
    training_type: str
):
    """
    Отправляет уведомление пользователю о завершении обучения
    ИСПРАВЛЕНО: Добавлен параметр training_type и улучшено логирование
    """
    try:
        request_id = webhook_data.get("request_id")
        logger.info(f"[NOTIFICATION] Начинаем отправку уведомления для {request_id}")
        
        # Находим аватар по request_id
        training_service = AvatarTrainingService(session)
        avatar = await training_service._find_avatar_by_request_id(request_id)
        
        if not avatar:
            logger.warning(f"[NOTIFICATION] Аватар с request_id {request_id} не найден")
            return
        
        logger.info(f"[NOTIFICATION] Найден аватар: {avatar.name} (ID: {avatar.id})")
        
        # Получаем пользователя
        user_service = get_user_service_with_session(session)
        user = await user_service.get_user_by_id(avatar.user_id)
        
        if not user or not user.telegram_id:
            logger.warning(f"[NOTIFICATION] Пользователь не найден для аватара {avatar.id}")
            return
        
        logger.info(f"[NOTIFICATION] Найден пользователь: {user.telegram_id}")
        
        # Отправляем уведомление через Telegram
        bot = Bot(token=main_settings.TELEGRAM_TOKEN)
        
        try:
            # Формируем сообщение
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
            
            # Создаем кнопку для перехода в меню аватаров
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🎭 Мои аватары",
                    callback_data="avatar_gallery"
                )],
                [InlineKeyboardButton(
                    text="🎨 Создать изображение",
                    callback_data=f"avatar_generate:{avatar.id}"
                )]
            ])
            
            logger.info(f"[NOTIFICATION] Отправляем сообщение пользователю {user.telegram_id}")
            
            await bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            logger.info(f"[NOTIFICATION] ✅ Уведомление отправлено пользователю {user.telegram_id}")
            
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
