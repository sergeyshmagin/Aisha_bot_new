"""
Конфигурация pytest для интеграционных тестов
"""
import asyncio
import pytest
import pytest_asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Создает event loop для всей сессии тестов"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    yield loop
    
    # Очистка после завершения тестов
    try:
        _cancel_all_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(loop.shutdown_default_executor())
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def _cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Отменяет все pending задачи в event loop"""
    to_cancel = asyncio.all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, return_exceptions=True)
    )

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })


# Маркеры для разных типов тестов
pytest_markers = [
    "database: marks tests as database integration tests",
    "redis: marks tests as redis integration tests", 
    "minio: marks tests as minio integration tests",
    "integration: marks tests as full integration tests",
    "slow: marks tests as slow running tests"
]


def pytest_configure(config):
    """Конфигурация pytest"""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


# Настройки asyncio для pytest
pytest_plugins = ('pytest_asyncio',) 