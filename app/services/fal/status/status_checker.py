"""
Модуль проверки статуса обучения в FAL AI
"""
import asyncio
from typing import Dict, Any

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class FalStatusChecker:
    """Проверка статуса обучения в FAL AI"""
    
    def __init__(self):
        self.test_mode = settings.AVATAR_TEST_MODE
    
    async def get_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """
        Получает статус обучения модели
        
        Args:
            request_id: ID обучения FAL AI
            training_type: Тип обучения
            
        Returns:
            Dict[str, Any]: Статус обучения
        """
        try:
            if self.test_mode:
                # В тестовом режиме возвращаем мок статус
                return await self._get_mock_status(request_id, training_type)
            
            # TODO: Реализовать получение статуса через FAL API
            # В FAL AI пока нет прямого API для получения статуса
            # Статус приходит через webhook
            
            logger.warning(f"[FAL Status] Получение статуса {request_id} для типа {training_type} пока не реализовано")
            return {
                "status": "unknown",
                "message": "Status checking not implemented yet",
                "request_id": request_id,
                "training_type": training_type
            }
            
        except Exception as e:
            logger.exception(f"[FAL Status] Ошибка получения статуса {request_id} для типа {training_type}: {e}")
            return {
                "status": "error",
                "message": f"Error checking status: {str(e)}",
                "request_id": request_id,
                "training_type": training_type
            }
    
    async def _get_mock_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """
        Возвращает мок статус для тестового режима
        
        Args:
            request_id: ID запроса
            training_type: Тип обучения
            
        Returns:
            Dict[str, Any]: Мок статус
        """
        # Симулируем разные статусы в зависимости от request_id
        if "test_" in request_id:
            # Для тестовых запросов всегда возвращаем completed
            status_data = {
                "status": "completed",
                "progress": 100,
                "created_at": "2025-05-23T16:00:00Z",
                "updated_at": "2025-05-23T16:30:00Z",
                "completed_at": "2025-05-23T16:30:00Z",
                "message": f"Training completed successfully (test mode)",
                "request_id": request_id,
                "training_type": training_type,
                "model_url": f"https://fal.ai/models/test_model_{request_id}",
                "test_mode": True
            }
        else:
            # Для реальных запросов возвращаем статус на основе хеша
            request_hash = hash(request_id) % 100
            
            if request_hash < 20:
                # 20% - в процессе
                status_data = {
                    "status": "in_progress",
                    "progress": request_hash * 5,
                    "created_at": "2025-05-23T16:00:00Z",
                    "updated_at": "2025-05-23T16:15:00Z",
                    "message": f"Training in progress ({request_hash * 5}%)",
                    "request_id": request_id,
                    "training_type": training_type,
                    "test_mode": True
                }
            elif request_hash < 90:
                # 70% - завершено успешно
                status_data = {
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2025-05-23T16:00:00Z",
                    "updated_at": "2025-05-23T16:30:00Z",
                    "completed_at": "2025-05-23T16:30:00Z",
                    "message": "Training completed successfully",
                    "request_id": request_id,
                    "training_type": training_type,
                    "model_url": f"https://fal.ai/models/mock_model_{request_id}",
                    "test_mode": True
                }
            else:
                # 10% - ошибка
                status_data = {
                    "status": "failed",
                    "progress": 0,
                    "created_at": "2025-05-23T16:00:00Z",
                    "updated_at": "2025-05-23T16:10:00Z",
                    "failed_at": "2025-05-23T16:10:00Z",
                    "message": "Training failed (mock error)",
                    "error": "Mock training error for testing",
                    "request_id": request_id,
                    "training_type": training_type,
                    "test_mode": True
                }
        
        logger.info(f"[FAL Status] Мок статус для {request_id}: {status_data['status']}")
        return status_data
    
    def parse_webhook_status(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит данные webhook от FAL AI
        
        Args:
            webhook_data: Данные от webhook
            
        Returns:
            Dict[str, Any]: Обработанный статус
        """
        try:
            # Извлекаем основную информацию
            status = webhook_data.get("status", "unknown")
            request_id = webhook_data.get("request_id", "")
            
            # Обрабатываем разные типы статусов
            if status == "completed":
                return {
                    "status": "completed",
                    "progress": 100,
                    "message": "Training completed successfully",
                    "request_id": request_id,
                    "model_url": webhook_data.get("model_url"),
                    "completed_at": webhook_data.get("completed_at"),
                    "webhook_data": webhook_data
                }
            elif status == "failed":
                return {
                    "status": "failed",
                    "progress": 0,
                    "message": webhook_data.get("error", "Training failed"),
                    "request_id": request_id,
                    "error": webhook_data.get("error"),
                    "failed_at": webhook_data.get("failed_at"),
                    "webhook_data": webhook_data
                }
            elif status == "in_progress":
                return {
                    "status": "in_progress",
                    "progress": webhook_data.get("progress", 0),
                    "message": f"Training in progress ({webhook_data.get('progress', 0)}%)",
                    "request_id": request_id,
                    "updated_at": webhook_data.get("updated_at"),
                    "webhook_data": webhook_data
                }
            else:
                return {
                    "status": status,
                    "message": webhook_data.get("message", f"Unknown status: {status}"),
                    "request_id": request_id,
                    "webhook_data": webhook_data
                }
                
        except Exception as e:
            logger.exception(f"[FAL Status] Ошибка парсинга webhook данных: {e}")
            return {
                "status": "error",
                "message": f"Error parsing webhook data: {str(e)}",
                "webhook_data": webhook_data
            } 