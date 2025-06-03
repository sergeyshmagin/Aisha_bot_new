"""
Обработчик webhook от FAL AI для обновления статусов обучения аватаров
"""
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..core.logger import get_logger
from ..database.connection import get_session_dependency
from ..services.avatar.training_service import AvatarTrainingService

logger = get_logger(__name__)


class FalWebhookHandler:
    """
    Обработчик webhook уведомлений от FAL AI
    
    Принимает статусы обучения моделей и обновляет соответствующие аватары в БД
    """

    async def handle_status_update(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает webhook от FAL AI с обновлением статуса обучения
        
        Args:
            webhook_data: Данные от FAL AI
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        try:
            logger.info(f"[FAL WEBHOOK] Получен webhook: {webhook_data}")
            
            # Получаем сессию БД
            session = await get_session_dependency()
            training_service = AvatarTrainingService(session)
            
            # Обрабатываем webhook
            success = await training_service.handle_webhook(webhook_data)
            
            if success:
                return {
                    "status": "success",
                    "message": "Webhook обработан успешно"
                }
            else:
                return {
                    "status": "error", 
                    "message": "Ошибка обработки webhook"
                }
                
        except Exception as e:
            logger.exception(f"[FAL WEBHOOK] Критическая ошибка обработки webhook: {e}")
            return {
                "status": "error",
                "message": f"Внутренняя ошибка: {str(e)}"
            }

    async def setup_webhook_routes(self, app: FastAPI):
        """
        Настраивает маршруты webhook для FAL AI
        
        Args:
            app: FastAPI приложение
        """
        
        @app.post("/webhook/fal/status")
        async def fal_status_webhook(request: Request, background_tasks: BackgroundTasks):
            """
            Endpoint для получения webhook от FAL AI
            """
            try:
                # Получаем данные из webhook
                webhook_data = await request.json()
                
                # Запускаем обработку в фоне для быстрого ответа
                background_tasks.add_task(
                    self.handle_status_update,
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

        logger.info("[FAL WEBHOOK] Маршруты webhook настроены: POST /webhook/fal/status")


# Глобальный экземпляр обработчика
fal_webhook_handler = FalWebhookHandler() 