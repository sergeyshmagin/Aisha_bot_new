## Интеграционные тесты с Redis

- Для интеграционных тестов требуется реальный сервер Redis (docker, локальный или внешний).
- Все параметры подключения задаются через переменные окружения (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`).
- Для pub/sub тестов используется polling для стабильности.
- Пример запуска:

```bash
set REDIS_HOST=192.168.0.3 && set REDIS_PORT=6379 && set REDIS_PASSWORD=<ваш_пароль> && python -m pytest frontend_bot/tests/shared/test_redis_integration.py -v
```

## Мокирование Redis для unit-тестов

- Для unit-тестов допускается мокать методы RedisClient через unittest.mock или pytest-mock.
- Интеграционные тесты всегда используют реальный сервер.
