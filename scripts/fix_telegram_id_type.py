"""
Скрипт для исправления типа поля telegram_id в таблице users
"""
import asyncio
import asyncpg
import logging
import os
import sys

# Добавляем корневую директорию в sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from app.core.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def fix_telegram_id_type():
    """Исправляет тип поля telegram_id в таблице users с INTEGER на VARCHAR"""
    logger.info("Начинаем исправление типа поля telegram_id...")
    
    # Получаем строку подключения к базе данных без asyncpg, чтобы использовать напрямую asyncpg
    db_url = str(settings.DATABASE_URL).replace('+asyncpg', '')
    
    try:
        # Подключаемся к базе данных
        logger.info(f"Подключаемся к базе данных: {db_url}")
        conn = await asyncpg.connect(db_url)
        
        try:
            # Проверяем текущий тип поля telegram_id
            logger.info("Проверяем текущий тип поля telegram_id...")
            column_type = await conn.fetchval(
                """
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'telegram_id'
                """
            )
            logger.info(f"Текущий тип поля telegram_id: {column_type}")
            
            if column_type.lower() == 'character varying':
                logger.info("Тип поля telegram_id уже VARCHAR, исправление не требуется.")
                return
            
            # Начинаем транзакцию
            async with conn.transaction():
                # Изменяем тип поля telegram_id напрямую
                logger.info("Изменяем тип поля telegram_id на VARCHAR(50)...")
                # Сначала удаляем индекс, если он есть
                await conn.execute("DROP INDEX IF EXISTS ix_users_telegram_id")
                
                # Изменяем тип поля telegram_id напрямую
                await conn.execute("ALTER TABLE users ALTER COLUMN telegram_id TYPE VARCHAR(50) USING telegram_id::text")
                
                # Создаем индекс и ограничение уникальности
                logger.info("Создаем индекс и ограничение уникальности...")
                await conn.execute("CREATE UNIQUE INDEX ix_users_telegram_id ON users (telegram_id)")
                
            logger.info("Тип поля telegram_id успешно изменен на VARCHAR(50).")
            
        finally:
            # Закрываем соединение
            await conn.close()
            logger.info("Соединение с базой данных закрыто.")
            
    except Exception as e:
        logger.error(f"Ошибка при исправлении типа поля telegram_id: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(fix_telegram_id_type())
