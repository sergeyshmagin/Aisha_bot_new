"""
Упрощенный FastAPI сервер для обработки webhook от FAL AI
На основе рабочего кода из архива
"""
import os
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from aiogram import Bot
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получаем настройки из переменных окружения  
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FAL_API_KEY = os.getenv("FAL_API_KEY", "")

# Создаем движок БД
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=3,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session():
    """Контекстный менеджер для БД"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Создаем FastAPI приложение
app = FastAPI(title="Aisha Bot Webhook API", version="2.0.0")

# Bot instance
bot_instance = None

async def get_bot() -> Optional[Bot]:
    """Получает Bot instance"""
    global bot_instance
    if bot_instance is None and TELEGRAM_BOT_TOKEN:
        bot_instance = Bot(token=TELEGRAM_BOT_TOKEN)
    return bot_instance

async def send_notification(user_telegram_id: str, message: str):
    """Отправляет уведомление пользователю"""
    try:
        bot = await get_bot()
        if bot:
            await bot.send_message(chat_id=user_telegram_id, text=message)
            logger.info(f"✅ Уведомление отправлено пользователю {user_telegram_id}")
    except Exception as e:
        logger.exception(f"❌ Ошибка отправки уведомления: {e}")

@app.post("/api/v1/avatar/status_update")
async def fal_status_webhook(request: Request, background_tasks: BackgroundTasks):
    """Endpoint для webhook от FAL AI"""
    try:
        webhook_data = await request.json()
        logger.info(f"[FAL WEBHOOK] Получен webhook: {webhook_data}")
        
        # Обрабатываем в фоне
        background_tasks.add_task(handle_fal_webhook, webhook_data)
        
        return JSONResponse(
            content={"status": "received", "message": "webhook processed"},
            status_code=200
        )
        
    except Exception as e:
        logger.exception(f"[FAL WEBHOOK] Ошибка: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook format")

async def handle_fal_webhook(webhook_data: Dict[str, Any]) -> bool:
    """Обрабатывает webhook от FAL AI"""
    try:
        logger.info(f"[FAL WEBHOOK] Обрабатываем: {webhook_data}")
        
        status = webhook_data.get("status")
        request_id = webhook_data.get("request_id") or webhook_data.get("finetune_id")
        
        if status == "completed" and request_id:
            # Простая обработка - находим в БД и отправляем уведомление
            async with get_session() as session:
                # Упрощенный запрос без импорта моделей
                result = await session.execute(
                    select("avatars.user_id", "avatars.name")
                    .select_from("avatars")
                    .where("avatars.fal_request_id = :request_id")
                    .params(request_id=request_id)
                )
                row = result.first()
                
                if row:
                    user_id, avatar_name = row
                    
                    # Получаем telegram_id пользователя
                    user_result = await session.execute(
                        select("users.telegram_id")
                        .select_from("users") 
                        .where("users.id = :user_id")
                        .params(user_id=user_id)
                    )
                    user_row = user_result.first()
                    
                    if user_row and user_row[0]:
                        message = f"🎉 Ваш аватар '{avatar_name}' готов! Обучение завершено успешно."
                        await send_notification(user_row[0], message)
                        
                        logger.info(f"[FAL WEBHOOK] Успешно обработан webhook для аватара {avatar_name}")
                    else:
                        logger.warning(f"[FAL WEBHOOK] Telegram ID не найден для пользователя {user_id}")
                else:
                    logger.warning(f"[FAL WEBHOOK] Аватар с request_id {request_id} не найден")
        
        return True
        
    except Exception as e:
        logger.exception(f"[FAL WEBHOOK] Критическая ошибка: {e}")
        return False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "webhook-api", "database": "connected"}

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Aisha Bot Webhook API", "version": "2.0.0"}

@app.post("/api/v1/avatar/test_webhook")
async def test_webhook(request: Request):
    """Тестовый webhook endpoint"""
    try:
        data = await request.json()
        logger.info(f"[TEST WEBHOOK] Получен: {data}")
        return {"status": "test_received", "data": data}
    except Exception as e:
        logger.error(f"[TEST WEBHOOK] Ошибка: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 