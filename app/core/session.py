"""
Управление сессиями базы данных
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Создаем движок с пулом соединений
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный контекстный менеджер для получения сессии БД
    
    Yields:
        AsyncSession: Сессия БД
    """
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

async def close_db_connection():
    """Корректно закрывает все соединения с БД"""
    try:
        logger.info("Закрытие соединений с базой данных...")
        await engine.dispose()
        logger.info("Соединения с базой данных закрыты")
    except Exception as e:
        logger.error(f"Ошибка при закрытии соединений с БД: {e}")

# Регистрируем обработчик сигналов
def register_shutdown_handlers():
    """Регистрирует обработчики для корректного завершения работы"""
    import signal
    
    def handle_shutdown(signum, frame):
        """Обработчик сигналов завершения"""
        logger.info(f"Получен сигнал {signum}, начинаем корректное завершение...")
        
        # Создаем новый event loop для асинхронных операций
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Закрываем соединения с БД
            loop.run_until_complete(close_db_connection())
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединений: {e}")
        finally:
            loop.close()
            logger.info("Завершение работы завершено")
            exit(0)
    
    # Регистрируем обработчики для SIGINT и SIGTERM
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

# Регистрируем обработчики при импорте модуля
register_shutdown_handlers() 