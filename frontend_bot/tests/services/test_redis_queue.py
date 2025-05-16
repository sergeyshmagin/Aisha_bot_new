"""
Тесты для RedisQueue.
"""

import pytest
from datetime import datetime
import json

from frontend_bot.services.redis_queue import RedisQueue
from frontend_bot.shared.redis_client import redis_client

@pytest.fixture
async def queue():
    """Фикстура для создания очереди."""
    queue = RedisQueue("test_queue")
    yield queue
    await queue.clear()

@pytest.mark.asyncio
async def test_push_and_pop(queue):
    """Тест добавления и извлечения задачи."""
    # Добавляем задачу
    task = {"type": "test", "data": "test_data"}
    assert await queue.push(task)
    
    # Извлекаем задачу
    popped_task = await queue.pop()
    assert popped_task is not None
    assert popped_task["type"] == "test"
    assert popped_task["data"] == "test_data"
    assert "created_at" in popped_task
    assert popped_task["status"] == "pending"

@pytest.mark.asyncio
async def test_complete_task(queue):
    """Тест отметки задачи как выполненной."""
    # Добавляем задачу
    task = {"type": "test", "data": "test_data", "task_id": "test_1"}
    await queue.push(task)
    
    # Извлекаем задачу
    popped_task = await queue.pop()
    assert popped_task is not None
    
    # Отмечаем как выполненную
    assert await queue.complete("test_1")
    
    # Проверяем что задача удалена из processing
    processing_tasks = await redis_client.lrange(queue._processing_name, 0, -1)
    assert len(processing_tasks) == 0

@pytest.mark.asyncio
async def test_fail_task(queue):
    """Тест отметки задачи как неудачной."""
    # Добавляем задачу
    task = {"type": "test", "data": "test_data", "task_id": "test_1"}
    await queue.push(task)
    
    # Извлекаем задачу
    popped_task = await queue.pop()
    assert popped_task is not None
    
    # Отмечаем как неудачную
    error = "Test error"
    assert await queue.fail("test_1", error)
    
    # Проверяем что задача в списке неудачных
    failed_tasks = await queue.get_failed_tasks()
    assert len(failed_tasks) == 1
    assert failed_tasks[0]["task_id"] == "test_1"
    assert failed_tasks[0]["error"] == error
    assert "failed_at" in failed_tasks[0]

@pytest.mark.asyncio
async def test_retry_failed_task(queue):
    """Тест повторного выполнения неудачной задачи."""
    # Добавляем задачу
    task = {"type": "test", "data": "test_data", "task_id": "test_1"}
    await queue.push(task)
    
    # Извлекаем и отмечаем как неудачную
    popped_task = await queue.pop()
    await queue.fail("test_1", "Test error")
    
    # Повторяем выполнение
    assert await queue.retry_failed_task("test_1")
    
    # Проверяем что задача вернулась в основную очередь
    popped_task = await queue.pop()
    assert popped_task is not None
    assert popped_task["task_id"] == "test_1"
    assert popped_task["retry_count"] == 1
    assert "last_retry" in popped_task

@pytest.mark.asyncio
async def test_get_queue_length(queue):
    """Тест получения длины очереди."""
    # Проверяем пустую очередь
    assert await queue.get_queue_length() == 0
    
    # Добавляем задачи
    for i in range(3):
        await queue.push({"type": "test", "data": f"test_{i}"})
    
    # Проверяем длину
    assert await queue.get_queue_length() == 3

@pytest.mark.asyncio
async def test_clear_queue(queue):
    """Тест очистки очереди."""
    # Добавляем задачи
    for i in range(3):
        await queue.push({"type": "test", "data": f"test_{i}"})
    
    # Очищаем очередь
    assert await queue.clear()
    
    # Проверяем что очередь пуста
    assert await queue.get_queue_length() == 0
    assert len(await queue.get_failed_tasks()) == 0 