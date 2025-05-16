"""
Модуль для работы с очередями задач через Redis.
"""

import json
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import CACHE_TTL

logger = logging.getLogger(__name__)

class RedisQueue:
    """Очередь задач на базе Redis."""
    
    def __init__(self, queue_name: str):
        """
        Инициализация очереди.
        
        Args:
            queue_name: Имя очереди
        """
        self._redis = redis_client
        self._queue_name = f"queue:{queue_name}"
        self._processing_name = f"{self._queue_name}:processing"
        self._ttl = CACHE_TTL
    
    async def push(self, task: Dict[str, Any]) -> bool:
        """
        Добавляет задачу в очередь.
        
        Args:
            task: Данные задачи
            
        Returns:
            bool: True если задача добавлена успешно
        """
        try:
            task["created_at"] = datetime.now().isoformat()
            task["status"] = "pending"
            return await self._redis.rpush(
                self._queue_name,
                json.dumps(task)
            )
        except Exception as e:
            logger.error(f"Error pushing task to queue {self._queue_name}: {e}")
            return False
    
    async def pop(self) -> Optional[Dict[str, Any]]:
        """
        Извлекает задачу из очереди.
        
        Returns:
            Optional[Dict[str, Any]]: Данные задачи или None
        """
        try:
            # Перемещаем задачу в processing
            task_data = await self._redis.rpoplpush(
                self._queue_name,
                self._processing_name
            )
            if not task_data:
                return None
                
            # Устанавливаем TTL для processing
            await self._redis.expire(self._processing_name, self._ttl)
            
            return json.loads(task_data)
        except Exception as e:
            logger.error(f"Error popping task from queue {self._queue_name}: {e}")
            return None
    
    async def complete(self, task_id: str) -> bool:
        """
        Отмечает задачу как выполненную.
        
        Args:
            task_id: ID задачи
            
        Returns:
            bool: True если задача отмечена успешно
        """
        try:
            # Удаляем задачу из processing
            return await self._redis.lrem(self._processing_name, 0, task_id)
        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return False
    
    async def fail(self, task_id: str, error: str) -> bool:
        """
        Отмечает задачу как неудачную.
        
        Args:
            task_id: ID задачи
            error: Сообщение об ошибке
            
        Returns:
            bool: True если задача отмечена успешно
        """
        try:
            # Удаляем задачу из processing
            await self._redis.lrem(self._processing_name, 0, task_id)
            
            # Добавляем в очередь неудачных задач
            failed_queue = f"{self._queue_name}:failed"
            task = {
                "task_id": task_id,
                "error": error,
                "failed_at": datetime.now().isoformat()
            }
            return await self._redis.rpush(failed_queue, json.dumps(task))
        except Exception as e:
            logger.error(f"Error marking task {task_id} as failed: {e}")
            return False
    
    async def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """
        Получает список неудачных задач.
        
        Returns:
            List[Dict[str, Any]]: Список неудачных задач
        """
        try:
            failed_queue = f"{self._queue_name}:failed"
            tasks = await self._redis.lrange(failed_queue, 0, -1)
            return [json.loads(task) for task in tasks]
        except Exception as e:
            logger.error(f"Error getting failed tasks from queue {self._queue_name}: {e}")
            return []
    
    async def retry_failed_task(self, task_id: str) -> bool:
        """
        Повторяет выполнение неудачной задачи.
        
        Args:
            task_id: ID задачи
            
        Returns:
            bool: True если задача добавлена успешно
        """
        try:
            failed_queue = f"{self._queue_name}:failed"
            tasks = await self._redis.lrange(failed_queue, 0, -1)
            
            for task_data in tasks:
                task = json.loads(task_data)
                if task["task_id"] == task_id:
                    # Удаляем из неудачных
                    await self._redis.lrem(failed_queue, 0, task_data)
                    
                    # Добавляем в основную очередь
                    task["retry_count"] = task.get("retry_count", 0) + 1
                    task["last_retry"] = datetime.now().isoformat()
                    return await self.push(task)
            
            return False
        except Exception as e:
            logger.error(f"Error retrying task {task_id}: {e}")
            return False
    
    async def get_queue_length(self) -> int:
        """
        Получает длину очереди.
        
        Returns:
            int: Количество задач в очереди
        """
        try:
            return await self._redis.llen(self._queue_name)
        except Exception as e:
            logger.error(f"Error getting queue length for {self._queue_name}: {e}")
            return 0
    
    async def clear(self) -> bool:
        """
        Очищает очередь.
        
        Returns:
            bool: True если очередь очищена успешно
        """
        try:
            await self._redis.delete(self._queue_name)
            await self._redis.delete(self._processing_name)
            await self._redis.delete(f"{self._queue_name}:failed")
            return True
        except Exception as e:
            logger.error(f"Error clearing queue {self._queue_name}: {e}")
            return False 