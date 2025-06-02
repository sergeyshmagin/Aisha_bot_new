"""
Тесты для интеграции с Redis
"""
import json
import pytest
import pytest_asyncio
from typing import AsyncGenerator

import redis.asyncio as redis

from app.core.config import settings@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Фикстура для подключения к Redis
    """
    redis_client = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB
    )
    try:
        yield redis_client
    finally:
        await redis_client.close()@pytest.mark.asyncio
async def test_redis_connection(redis_client: redis.Redis):
    """Тест подключения к Redis"""
    # Arrange & Act
    ping_result = await redis_client.ping()
    
    # Assert
    assert ping_result is True@pytest.mark.asyncio
async def test_redis_set_get(redis_client: redis.Redis):
    """Тест установки и получения значения из Redis"""
    # Arrange
    test_key = "test:key"
    test_value = "test_value"
    
    # Act
    await redis_client.set(test_key, test_value)
    result = await redis_client.get(test_key)
    
    # Assert
    assert result.decode("utf-8") == test_value
    
    # Cleanup
    await redis_client.delete(test_key)@pytest.mark.asyncio
async def test_redis_json(redis_client: redis.Redis):
    """Тест сохранения и получения JSON из Redis"""
    # Arrange
    test_key = "test:json"
    test_data = {
        "user_id": 123456789,
        "name": "Test User",
        "settings": {
            "language": "ru",
            "notifications": True
        }
    }
    
    # Act
    await redis_client.set(test_key, json.dumps(test_data))
    result = await redis_client.get(test_key)
    loaded_data = json.loads(result.decode("utf-8"))
    
    # Assert
    assert loaded_data == test_data
    assert loaded_data["user_id"] == 123456789
    assert loaded_data["settings"]["language"] == "ru"
    
    # Cleanup
    await redis_client.delete(test_key)@pytest.mark.asyncio
async def test_redis_ttl(redis_client: redis.Redis):
    """Тест установки TTL (Time To Live) для ключа в Redis"""
    # Arrange
    test_key = "test:ttl"
    test_value = "expires_soon"
    ttl_seconds = 10
    
    # Act
    await redis_client.set(test_key, test_value, ex=ttl_seconds)
    ttl_result = await redis_client.ttl(test_key)
    
    # Assert
    assert ttl_result <= ttl_seconds
    assert ttl_result > 0
    
    # Cleanup
    await redis_client.delete(test_key)@pytest.mark.asyncio
async def test_redis_hash(redis_client: redis.Redis):
    """Тест работы с хеш-таблицами в Redis"""
    # Arrange
    test_hash = "test:hash"
    test_fields = {
        "field1": "value1",
        "field2": "value2",
        "field3": "value3"
    }
    
    # Act
    await redis_client.hset(test_hash, mapping=test_fields)
    all_fields = await redis_client.hgetall(test_hash)
    field2 = await redis_client.hget(test_hash, "field2")
    
    # Assert
    assert {k.decode("utf-8"): v.decode("utf-8") for k, v in all_fields.items()} == test_fields
    assert field2.decode("utf-8") == "value2"
    
    # Cleanup
    await redis_client.delete(test_hash)
