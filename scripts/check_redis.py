import asyncio
import redis.asyncio as redis
import logging
from typing import Optional
from redis.retry import Retry
from redis.backoff import ExponentialBackoff

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Настройки Redis
REDIS_CONFIG = {
    "host": "192.168.0.3",
    "port": 6379,
    "db": 0,
    "password": "wd7QuwAbG0wtyoOOw3Sm",
    "ssl": False,
    "socket_timeout": 5.0,
    "socket_connect_timeout": 5.0,
    "retry_on_timeout": True,
    "max_connections": 10,
    "retry": Retry(ExponentialBackoff(), retries=3),  # добавляем backoff
}

async def check_redis_connection() -> bool:
    """
    Проверяет соединение с Redis.
    Возвращает True, если соединение успешно, иначе False.
    """
    redis_client: Optional[redis.Redis] = None
    try:
        # Подключение к Redis
        redis_client = redis.Redis(**REDIS_CONFIG)
        logger.info("Подключение к Redis...")

        # Проверка соединения (PING)
        ping_result = await redis_client.ping()
        logger.info(f"PING: {ping_result}")

        # Запись тестовых данных
        test_key = "test:connection"
        test_value = "Hello, Redis!"
        await redis_client.set(test_key, test_value)
        logger.info(f"Запись данных: {test_key} = {test_value}")

        # Чтение тестовых данных
        read_value = await redis_client.get(test_key)
        logger.info(f"Чтение данных: {test_key} = {read_value}")

        # Удаление тестовых данных
        await redis_client.delete(test_key)
        logger.info(f"Удаление данных: {test_key}")

        return True

    except redis.ConnectionError as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        return False
    except redis.TimeoutError as e:
        logger.error(f"Таймаут подключения к Redis: {e}")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        return False
    finally:
        if redis_client:
            await redis_client.close()
            logger.info("Соединение с Redis закрыто.")

async def main():
    """
    Основная функция для проверки Redis.
    """
    logger.info("Начало проверки Redis...")
    success = await check_redis_connection()
    if success:
        logger.info("Проверка Redis успешно завершена!")
    else:
        logger.error("Проверка Redis не удалась!")

if __name__ == "__main__":
    asyncio.run(main())
