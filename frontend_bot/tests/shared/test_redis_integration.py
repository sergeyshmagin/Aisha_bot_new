"""
Интеграционные тесты для Redis клиента.
Требует запущенный Redis сервер.
"""

import pytest
import json
from frontend_bot.shared.redis_client import RedisClient
import asyncio

@pytest.fixture
async def redis():
    """Фикстура для реального Redis клиента."""
    client = RedisClient()
    await client.init()
    yield client
    await client.close()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection(redis):
    """Тест подключения к Redis."""
    # Проверяем, что можем установить и получить значение
    await redis.set("test:connection", "ok")
    value = await redis.get("test:connection")
    assert value == "ok"
    await redis.delete("test:connection")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_hash_operations(redis):
    """Тест операций с хэш-таблицами."""
    # Тестируем установку и получение значений из хэш-таблицы
    await redis.hset("test:hash", "field1", "value1")
    await redis.hset("test:hash", "field2", "value2")
    
    # Получаем все значения
    all_values = await redis.hgetall("test:hash")
    assert all_values == {"field1": "value1", "field2": "value2"}
    
    # Получаем отдельное значение
    value = await redis.hget("test:hash", "field1")
    assert value == "value1"
    
    # Удаляем значение
    await redis.hdel("test:hash", "field1")
    value = await redis.hget("test:hash", "field1")
    assert value is None
    
    # Очищаем тестовые данные
    await redis.delete("test:hash")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_expiration(redis):
    """Тест TTL и истечения срока действия."""
    # Устанавливаем значение с TTL 1 секунда
    await redis.set("test:expire", "value", expire=1)
    
    # Проверяем, что значение существует
    exists = await redis.exists("test:expire")
    assert exists is True
    
    # Проверяем TTL
    ttl = await redis.ttl("test:expire")
    assert 0 <= ttl <= 1
    
    # Ждем 1 секунду
    await asyncio.sleep(1.1)
    
    # Проверяем, что значение истекло
    exists = await redis.exists("test:expire")
    assert exists is False

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_counter(redis):
    """Тест счетчиков."""
    # Увеличиваем счетчик
    value = await redis.incr("test:counter")
    assert value == 1
    
    value = await redis.incr("test:counter")
    assert value == 2
    
    # Уменьшаем счетчик
    value = await redis.decr("test:counter")
    assert value == 1
    
    # Очищаем тестовые данные
    await redis.delete("test:counter")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_json(redis):
    """Тест работы с JSON данными."""
    # Создаем тестовые данные
    test_data = {
        "name": "test",
        "values": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    # Сохраняем данные
    await redis.set("test:json", test_data)
    
    # Получаем данные
    value = await redis.get("test:json")
    loaded_data = json.loads(value)
    assert loaded_data == test_data
    
    # Очищаем тестовые данные
    await redis.delete("test:json")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_pubsub(redis):
    """Тест pub/sub функциональности."""
    pubsub = await redis.subscribe("test:channel")
    await asyncio.sleep(0.1)
    subscribers = await redis.publish("test:channel", "test message")
    assert subscribers == 1

    # Ждем сообщение с polling (до 1 сек)
    message = None
    for _ in range(10):
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message is not None:
            break
        await asyncio.sleep(0.1)
    assert message is not None
    assert message["data"] == "test message"

    await pubsub.unsubscribe("test:channel")
    await pubsub.close() 