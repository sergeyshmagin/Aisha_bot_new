"""
FastAPI сервер для обработки webhook от FAL AI
"""
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from aiogram import Bot

from app.core.config import settings
from app.core.logger import get_logger
from app.database.connection import get_session_dependency
from app.services.avatar.training_service import AvatarTrainingService
from app.services.user import get_user_service_with_session

logger = get_logger(__name__)

# Создаем FastAPI приложение
app = FastAPI(title="Aisha Bot API", version="1.0.0")

# Глобальный Bot instance для отправки уведомлений
bot_instance = None

async def get_bot() -> Bot:
    """Получает Bot instance для отправки уведомлений"""
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=settings.TELEGRAM_TOKEN)
    return bot_instance

async def send_avatar_ready_notification(user_telegram_id: str, avatar_name: str, training_type: str):
    """
    Отправляет уведомление пользователю о готовности аватара
    
    Args:
        user_telegram_id: Telegram ID пользователя
        avatar_name: Название аватара
        training_type: Тип обучения (portrait/style)
    """
    try:
        bot = await get_bot()
        
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
        
        await bot.send_message(
            chat_id=user_telegram_id,
            text=message,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Уведомление о готовности аватара отправлено пользователю {user_telegram_id}")
        
    except Exception as e:
        logger.exception(f"❌ Ошибка отправки уведомления пользователю {user_telegram_id}: {e}")

@app.post("/webhook/fal/status")
async def fal_status_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint для получения webhook от FAL AI о статусе обучения аватара
    """
    try:
        # Получаем данные из webhook
        webhook_data = await request.json()
        
        logger.info(f"[FAL WEBHOOK] Получен webhook: {webhook_data}")
        
        # Запускаем обработку в фоне для быстрого ответа
        background_tasks.add_task(
            handle_fal_webhook,
            webhook_data
        )
        
        # Быстро отвечаем FAL AI что webhook получен
        return JSONResponse(
            content={"status": "received"},
            status_code=200
        )
        
    except Exception as e:
        logger.exception(f"[FAL WEBHOOK] Ошибка получения webhook: {e}")
        raise HTTPException(
            status_code=400,
            detail="Некорректный формат webhook"
        )

async def handle_fal_webhook(webhook_data: Dict[str, Any]) -> bool:
    """
    Обрабатывает webhook от FAL AI и отправляет уведомления пользователям
    
    Args:
        webhook_data: Данные от FAL AI
        
    Returns:
        bool: True если webhook обработан успешно
    """
    try:
        logger.info(f"[FAL WEBHOOK] Начинаем обработку webhook: {webhook_data}")
        
        # Получаем сессию БД
        session = await get_session_dependency()
        training_service = AvatarTrainingService(session)
        user_service = get_user_service_with_session(session)
        
        # Обрабатываем webhook через существующий сервис
        success = await training_service.handle_webhook(webhook_data)
        
        if not success:
            logger.warning("[FAL WEBHOOK] Webhook не был обработан успешно")
            return False
        
        # Если обучение завершено - отправляем уведомление пользователю
        status = webhook_data.get("status")
        if status == "completed":
            # Извлекаем информацию из webhook
            request_id = webhook_data.get("request_id") or webhook_data.get("finetune_id")
            training_type = webhook_data.get("training_type", "portrait")
            
            if request_id:
                # Находим аватар по request_id
                avatar = await training_service._find_avatar_by_request_id(request_id)
                
                if avatar:
                    # Получаем пользователя
                    user = await user_service.get_user_by_id(avatar.user_id)
                    
                    if user and user.telegram_id:
                        # Отправляем уведомление
                        await send_avatar_ready_notification(
                            user_telegram_id=user.telegram_id,
                            avatar_name=avatar.name,
                            training_type=training_type
                        )
                        
                        logger.info(f"[FAL WEBHOOK] Уведомление отправлено пользователю {user.telegram_id}")
                    else:
                        logger.warning(f"[FAL WEBHOOK] Пользователь не найден для аватара {avatar.id}")
                else:
                    logger.warning(f"[FAL WEBHOOK] Аватар с request_id {request_id} не найден")
        
        return True
        
    except Exception as e:
        logger.exception(f"[FAL WEBHOOK] Критическая ошибка обработки webhook: {e}")
        return False

@app.get("/health")
async def health_check():
    """Проверка здоровья API сервера"""
    return {"status": "healthy", "service": "Aisha Bot API"}

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "Aisha Bot API Server", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
