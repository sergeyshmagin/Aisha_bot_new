"""
Полноценный FastAPI сервер для обработки webhook от FAL AI
Объединяет legacy код с современными подходами
"""
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from aiogram import Bot
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logger import get_logger
from app.core.database import get_session
from app.database.models.models import Avatar, AvatarStatus, User

logger = get_logger(__name__)

# =================== STARTUP & SHUTDOWN ===================

# Глобальный Bot instance для отправки уведомлений
bot_instance: Optional[Bot] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management для FastAPI приложения"""
    global bot_instance
    
    # Startup
    logger.info("🚀 Запуск webhook API сервера")
    
    # Инициализируем Bot
    if settings.TELEGRAM_TOKEN:
        bot_instance = Bot(token=settings.TELEGRAM_TOKEN)
        logger.info("🤖 Bot instance инициализирован")
    else:
        logger.warning("⚠️ TELEGRAM_TOKEN не найден")
    
    # Проверяем подключение к БД
    try:
        async with get_session() as session:
            await session.execute(select(1))
            logger.info("✅ Подключение к БД успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Остановка webhook API сервера")
    if bot_instance:
        await bot_instance.session.close()

# Создаем FastAPI приложение
app = FastAPI(
    title="Aisha Bot Webhook API", 
    version="2.0.0",
    description="Webhook API для обработки статусов обучения от FAL AI",
    lifespan=lifespan
)

# =================== DEPENDENCIES ===================

async def get_db() -> AsyncSession:
    """Dependency для получения сессии БД"""
    async with get_session() as session:
        yield session

# =================== UTILITY FUNCTIONS ===================

async def send_avatar_ready_notification(user_telegram_id: str, avatar_name: str, training_type: str):
    """
    Отправляет уведомление пользователю о готовности аватара
    
    Args:
        user_telegram_id: Telegram ID пользователя
        avatar_name: Название аватара  
        training_type: Тип обучения (portrait/style)
    """
    try:
        if not bot_instance:
            logger.warning("⚠️ Bot instance не инициализирован")
            return
            
        # Формируем сообщение в зависимости от типа обучения
        if training_type == "portrait":
            emoji = "🎭"
            type_name = "Портретный"
        else:
            emoji = "🎨"
            type_name = "Художественный"
        
        message = (
            f"🎉 Ваш аватар готов!\n\n"
            f"{emoji} **{avatar_name}** ({type_name} стиль)\n"
            f"✅ Обучение завершено успешно\n\n"
            f"Теперь вы можете использовать аватар для генерации изображений!"
        )
        
        await bot_instance.send_message(
            chat_id=user_telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Уведомление о готовности аватара отправлено пользователю {user_telegram_id}")
        
    except Exception as e:
        logger.exception(f"❌ Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")

async def find_avatar_by_request_id(session: AsyncSession, request_id: str) -> Optional[Avatar]:
    """
    Находит аватар по request_id
    
    Args:
        session: Сессия БД
        request_id: ID запроса FAL AI
        
    Returns:
        Avatar или None
    """
    try:
        query = select(Avatar).where(Avatar.fal_request_id == request_id)
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if avatar:
            logger.info(f"🔍 Найден аватар {avatar.name} (ID: {avatar.id}) для request_id: {request_id}")
        else:
            logger.warning(f"⚠️ Аватар с request_id {request_id} не найден")
            
        return avatar
        
    except Exception as e:
        logger.exception(f"❌ Ошибка поиска аватара по request_id {request_id}: {e}")
        return None

async def update_avatar_status_from_webhook(
    session: AsyncSession, 
    avatar: Avatar, 
    webhook_data: Dict[str, Any]
) -> bool:
    """
    Обновляет статус аватара на основе webhook данных
    
    Args:
        session: Сессия БД
        avatar: Аватар для обновления
        webhook_data: Данные webhook
        
    Returns:
        bool: True если обновление успешно
    """
    try:
        status = webhook_data.get("status", "unknown")
        
        # Маппинг статусов FAL AI в наши статусы
        status_mapping = {
            "IN_QUEUE": AvatarStatus.TRAINING,
            "IN_PROGRESS": AvatarStatus.TRAINING,
            "COMPLETED": AvatarStatus.COMPLETED,
            "FAILED": AvatarStatus.ERROR,
            "CANCELLED": AvatarStatus.CANCELLED,
            "completed": AvatarStatus.COMPLETED,
            "failed": AvatarStatus.ERROR,
            "cancelled": AvatarStatus.CANCELLED,
        }
        
        new_status = status_mapping.get(status, AvatarStatus.TRAINING)
        
        # Подготавливаем данные для обновления
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow(),
            "last_status_check": datetime.utcnow()
        }
        
        # Обновляем прогресс если есть
        if "progress" in webhook_data:
            progress = webhook_data.get("progress", 0)
            if isinstance(progress, (int, float)) and 0 <= progress <= 100:
                update_data["training_progress"] = int(progress)
        
        # Обрабатываем завершение обучения
        if new_status == AvatarStatus.COMPLETED:
            update_data["training_completed_at"] = datetime.utcnow()
            update_data["training_progress"] = 100
            
            # Сохраняем данные результата если есть
            if "result" in webhook_data:
                result = webhook_data["result"]
                
                # Извлекаем URL LoRA файла
                if "diffusers_lora_file" in result:
                    update_data["diffusers_lora_file_url"] = result["diffusers_lora_file"]
                
                # Извлекаем config файл
                if "config_file" in result:
                    update_data["config_file_url"] = result["config_file"]
            
            # Обновляем fal_response_data
            current_data = avatar.fal_response_data or {}
            current_data.update({
                "webhook_completion": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": status,
                    "data": webhook_data
                }
            })
            update_data["fal_response_data"] = current_data
            
        # Обрабатываем ошибку
        elif new_status == AvatarStatus.ERROR:
            error_message = webhook_data.get("error", "Training failed")
            update_data["training_error"] = error_message
            
            # Обновляем fal_response_data
            current_data = avatar.fal_response_data or {}
            current_data.update({
                "webhook_error": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": error_message,
                    "data": webhook_data
                }
            })
            update_data["fal_response_data"] = current_data
        
        # Применяем обновления
        stmt = update(Avatar).where(Avatar.id == avatar.id).values(**update_data)
        await session.execute(stmt)
        await session.commit()
        
        logger.info(f"✅ Статус аватара {avatar.name} обновлен: {avatar.status} -> {new_status}")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Ошибка обновления статуса аватара {avatar.id}: {e}")
        await session.rollback()
        return False

async def get_user_by_avatar(session: AsyncSession, avatar: Avatar) -> Optional[User]:
    """
    Получает пользователя по аватару
    
    Args:
        session: Сессия БД
        avatar: Аватар
        
    Returns:
        User или None
    """
    try:
        query = select(User).where(User.id == avatar.user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        return user
        
    except Exception as e:
        logger.exception(f"❌ Ошибка получения пользователя для аватара {avatar.id}: {e}")
        return None

# =================== WEBHOOK HANDLERS ===================

async def handle_fal_webhook(webhook_data: Dict[str, Any]) -> bool:
    """
    Обрабатывает webhook от FAL AI
    
    Args:
        webhook_data: Данные от FAL AI
        
    Returns:
        bool: True если webhook обработан успешно
    """
    try:
        logger.info(f"🔄 Начинаем обработку FAL webhook: {webhook_data}")
        
        # Извлекаем request_id из различных возможных полей
        request_id = (
            webhook_data.get("request_id") or
            webhook_data.get("finetune_id") or
            webhook_data.get("id")
        )
        
        if not request_id:
            logger.error("❌ request_id не найден в webhook данных")
            return False
        
        # Получаем статус
        status = webhook_data.get("status", "unknown")
        logger.info(f"🔄 Обрабатываем request_id: {request_id}, статус: {status}")
        
        # Работаем с БД
        async with get_session() as session:
            # Находим аватар
            avatar = await find_avatar_by_request_id(session, request_id)
            
            if not avatar:
                logger.warning(f"⚠️ Аватар с request_id {request_id} не найден")
                return False
            
            # Обновляем статус аватара
            success = await update_avatar_status_from_webhook(session, avatar, webhook_data)
            
            if not success:
                logger.error(f"❌ Не удалось обновить статус аватара {avatar.id}")
                return False
            
            # Если обучение завершено - отправляем уведомление
            if status in ["COMPLETED", "completed"]:
                user = await get_user_by_avatar(session, avatar)
                
                if user and user.telegram_id:
                    training_type = avatar.training_type.value if avatar.training_type else "portrait"
                    
                    await send_avatar_ready_notification(
                        user_telegram_id=user.telegram_id,
                        avatar_name=avatar.name,
                        training_type=training_type
                    )
                    
                    logger.info(f"✅ Уведомление отправлено пользователю {user.telegram_id}")
                else:
                    logger.warning(f"⚠️ Пользователь не найден для аватара {avatar.id}")
        
        logger.info(f"✅ Webhook успешно обработан для request_id: {request_id}")
        return True
        
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка обработки webhook: {e}")
        return False

# =================== API ENDPOINTS ===================

@app.post("/webhook/fal/status")
async def fal_status_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Основной endpoint для получения webhook от FAL AI о статусе обучения аватара
    """
    try:
        # Получаем данные из webhook
        webhook_data = await request.json()
        
        logger.info(f"📨 Получен FAL webhook: {webhook_data}")
        
        # Запускаем обработку в фоне для быстрого ответа
        background_tasks.add_task(handle_fal_webhook, webhook_data)
        
        # Быстро отвечаем FAL AI что webhook получен
        return JSONResponse(
            content={
                "status": "received",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": webhook_data.get("request_id") or webhook_data.get("id")
            },
            status_code=200
        )
        
    except Exception as e:
        logger.exception(f"❌ Ошибка получения webhook: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Некорректный формат webhook: {str(e)}"
        )

@app.post("/webhook/fal/portrait")
async def fal_portrait_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Специфичный endpoint для flux-lora-portrait-trainer webhook
    """
    try:
        webhook_data = await request.json()
        
        # Добавляем тип обучения для идентификации
        webhook_data["training_type"] = "portrait"
        
        logger.info(f"📨 Получен FAL portrait webhook: {webhook_data}")
        
        background_tasks.add_task(handle_fal_webhook, webhook_data)
        
        return JSONResponse(
            content={
                "status": "received",
                "training_type": "portrait",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": webhook_data.get("request_id") or webhook_data.get("id")
            },
            status_code=200
        )
        
    except Exception as e:
        logger.exception(f"❌ Ошибка получения portrait webhook: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Некорректный формат portrait webhook: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Проверка здоровья API сервера"""
    try:
        # Проверяем подключение к БД
        async with get_session() as session:
            await session.execute(select(1))
            db_status = "healthy"
    except Exception as e:
        logger.error(f"❌ Проблема с БД: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": "Aisha Bot Webhook API",
        "version": "2.0.0",
        "database": db_status,
        "bot_initialized": bot_instance is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Aisha Bot Webhook API Server",
        "version": "2.0.0",
        "endpoints": {
            "main_webhook": "/webhook/fal/status",
            "portrait_webhook": "/webhook/fal/portrait",
            "health": "/health"
        }
    }

@app.get("/avatars/training")
async def get_training_avatars(session: AsyncSession = Depends(get_db)):
    """
    Получает список аватаров в процессе обучения
    """
    try:
        query = select(Avatar).where(Avatar.status == AvatarStatus.TRAINING)
        result = await session.execute(query)
        avatars = result.scalars().all()
        
        avatars_data = []
        for avatar in avatars:
            avatars_data.append({
                "id": str(avatar.id),
                "name": avatar.name,
                "status": avatar.status.value,
                "progress": avatar.training_progress,
                "request_id": avatar.fal_request_id,
                "training_type": avatar.training_type.value if avatar.training_type else None,
                "started_at": avatar.training_started_at.isoformat() if avatar.training_started_at else None,
                "last_check": avatar.last_status_check.isoformat() if avatar.last_status_check else None
            })
        
        return {
            "count": len(avatars_data),
            "avatars": avatars_data
        }
        
    except Exception as e:
        logger.exception(f"❌ Ошибка получения тренирующихся аватаров: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    ) 