"""
Тесты для Redis клиента.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from frontend_bot.shared.redis_client import RedisClient, redis_client

@pytest.fixture
async def mock_redis():
    """Фикстура для мока Redis клиента."""
    with patch('redis.asyncio.Redis') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
async def client(mock_redis):
    """Фикстура для тестируемого клиента."""
    client = RedisClient()
    await client.init()
    return client

@pytest.mark.asyncio
async def test_init(client, mock_redis):
    """Тест инициализации клиента."""
    mock_redis.ping.assert_called_once()
    
@pytest.mark.asyncio
async def test_close(client, mock_redis):
    """Тест закрытия соединения."""
    await client.close()
    mock_redis.close.assert_called_once()
    
@pytest.mark.asyncio
async def test_get(client, mock_redis):
    """Тест получения значения."""
    mock_redis.get.return_value = "test_value"
    result = await client.get("test_key")
    assert result == "test_value"
    mock_redis.get.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_set(client, mock_redis):
    """Тест установки значения."""
    mock_redis.set.return_value = True
    result = await client.set("test_key", "test_value", expire=60)
    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=60)
    
@pytest.mark.asyncio
async def test_delete(client, mock_redis):
    """Тест удаления ключа."""
    mock_redis.delete.return_value = 1
    result = await client.delete("test_key")
    assert result is True
    mock_redis.delete.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_exists(client, mock_redis):
    """Тест проверки существования ключа."""
    mock_redis.exists.return_value = 1
    result = await client.exists("test_key")
    assert result is True
    mock_redis.exists.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_ttl(client, mock_redis):
    """Тест получения TTL."""
    mock_redis.ttl.return_value = 60
    result = await client.ttl("test_key")
    assert result == 60
    mock_redis.ttl.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_incr(client, mock_redis):
    """Тест инкремента."""
    mock_redis.incr.return_value = 2
    result = await client.incr("test_key")
    assert result == 2
    mock_redis.incr.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_decr(client, mock_redis):
    """Тест декремента."""
    mock_redis.decr.return_value = 0
    result = await client.decr("test_key")
    assert result == 0
    mock_redis.decr.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_hget(client, mock_redis):
    """Тест получения значения из хэш-таблицы."""
    mock_redis.hget.return_value = "test_value"
    result = await client.hget("test_hash", "test_key")
    assert result == "test_value"
    mock_redis.hget.assert_called_once_with("test_hash", "test_key")
    
@pytest.mark.asyncio
async def test_hset(client, mock_redis):
    """Тест установки значения в хэш-таблицу."""
    mock_redis.hset.return_value = 1
    result = await client.hset("test_hash", "test_key", "test_value")
    assert result == 1
    mock_redis.hset.assert_called_once_with("test_hash", "test_key", "test_value")
    
@pytest.mark.asyncio
async def test_hgetall(client, mock_redis):
    """Тест получения всех значений из хэш-таблицы."""
    mock_redis.hgetall.return_value = {"key1": "value1", "key2": "value2"}
    result = await client.hgetall("test_hash")
    assert result == {"key1": "value1", "key2": "value2"}
    mock_redis.hgetall.assert_called_once_with("test_hash")
    
@pytest.mark.asyncio
async def test_hdel(client, mock_redis):
    """Тест удаления ключей из хэш-таблицы."""
    mock_redis.hdel.return_value = 2
    result = await client.hdel("test_hash", "key1", "key2")
    assert result == 2
    mock_redis.hdel.assert_called_once_with("test_hash", "key1", "key2")
    
@pytest.mark.asyncio
async def test_publish(client, mock_redis):
    """Тест публикации сообщения."""
    mock_redis.publish.return_value = 1
    result = await client.publish("test_channel", "test_message")
    assert result == 1
    mock_redis.publish.assert_called_once_with("test_channel", "test_message")
    
@pytest.mark.asyncio
async def test_subscribe(client, mock_redis):
    """Тест подписки на каналы."""
    from unittest.mock import MagicMock, AsyncMock
    pubsub = MagicMock(spec=object)
    pubsub.subscribe = AsyncMock()
    mock_redis.pubsub = MagicMock(return_value=pubsub)
    result = await client.subscribe("test_channel1", "test_channel2")
    assert result == pubsub
    mock_redis.pubsub.assert_called_once()
    pubsub.subscribe.assert_called_once_with("test_channel1", "test_channel2")
    
@pytest.mark.asyncio
async def test_set_json(client, mock_redis):
    """Тест сохранения JSON-данных."""
    test_data = {"key": "value", "number": 42}
    mock_redis.set.return_value = True
    result = await client.set_json("test_key", test_data, expire=60)
    assert result is True
    mock_redis.set.assert_called_once_with(
        "test_key",
        json.dumps(test_data),
        ex=60
    )
    
@pytest.mark.asyncio
async def test_get_json(client, mock_redis):
    """Тест получения JSON-данных."""
    test_data = {"key": "value", "number": 42}
    mock_redis.get.return_value = json.dumps(test_data)
    result = await client.get_json("test_key")
    assert result == test_data
    mock_redis.get.assert_called_once_with("test_key")
    
@pytest.mark.asyncio
async def test_get_json_none(client, mock_redis):
    """Тест получения JSON-данных при отсутствии ключа."""
    mock_redis.get.return_value = None
    result = await client.get_json("test_key")
    assert result is None
    mock_redis.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_set_string(client, mock_redis):
    """Тест установки строкового значения."""
    mock_redis.set.return_value = True
    result = await client.set("test_key", "test_value")
    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=None)

@pytest.mark.asyncio
async def test_set_dict(client, mock_redis):
    """Тест установки словаря."""
    test_dict = {"key": "value"}
    mock_redis.set.return_value = True
    result = await client.set("test_key", test_dict)
    assert result is True
    mock_redis.set.assert_called_once_with("test_key", json.dumps(test_dict), ex=None)

@pytest.mark.asyncio
async def test_set_with_expire(client, mock_redis):
    """Тест установки значения с TTL."""
    mock_redis.set.return_value = True
    result = await client.set("test_key", "test_value", expire=60)
    assert result is True
    mock_redis.set.assert_called_once_with("test_key", "test_value", ex=60)

@pytest.mark.asyncio
async def test_connection_error():
    """Тест обработки ошибки подключения."""
    with patch("redis.asyncio.Redis", side_effect=Exception("Connection error")):
        client = RedisClient()
        with pytest.raises(Exception) as exc_info:
            await client.init()
        assert "Connection error" in str(exc_info.value) 