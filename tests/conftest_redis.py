"""Фикстуры для тестирования Redis."""

import pytest
from unittest.mock import AsyncMock, patch
from frontend_bot.shared.redis_client import RedisClient

@pytest.fixture
async def mock_redis():
    """Фикстура для мока Redis."""
    with patch('frontend_bot.shared.redis_client.RedisClient') as mock:
        # Создаем мок для Redis клиента
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.delete = AsyncMock(return_value=True)
        mock_client.exists = AsyncMock(return_value=False)
        mock_client.keys = AsyncMock(return_value=[])
        mock_client.incr = AsyncMock(return_value=1)
        mock_client.decr = AsyncMock(return_value=0)
        mock_client.expire = AsyncMock(return_value=True)
        mock_client.ttl = AsyncMock(return_value=3600)
        
        # Настраиваем мок
        mock.return_value = mock_client
        mock.return_value._client = mock_client
        
        # Создаем экземпляр RedisClient
        client = RedisClient()
        client._client = mock_client
        
        yield client
        
        # Очищаем после теста
        await client.close() 