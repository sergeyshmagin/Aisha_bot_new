"""
Скрипт для проверки структуры таблицы users
"""
import asyncio
import asyncpg
import os
import sys
import logging

# Добавляем корневую директорию в sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

from aisha_v2.app.core.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def check_users_table():
    """Проверяет структуру таблицы users"""
    logger.info("Проверяем структуру таблицы users...")
    
    # Получаем строку подключения к базе данных без asyncpg, чтобы использовать напрямую asyncpg
    db_url = str(settings.DATABASE_URL).replace('+asyncpg', '')
    
    try:
        # Подключаемся к базе данных
        logger.info(f"Подключаемся к базе данных: {db_url}")
        conn = await asyncpg.connect(db_url)
        
        try:
            # Получаем информацию о столбцах таблицы users
            logger.info("Получаем информацию о столбцах таблицы users...")
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """)
            
            logger.info("Структура таблицы users:")
            for col in columns:
                logger.info(f"{col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
        finally:
            # Закрываем соединение
            await conn.close()
            logger.info("Соединение с базой данных закрыто.")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке структуры таблицы users: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(check_users_table())
