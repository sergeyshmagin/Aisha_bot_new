"""
Скрипт для добавления колонки timezone в таблицу users
"""
import asyncio
import asyncpg
from aisha_v2.app.core.config import settings

async def add_timezone_column():
    # Подключаемся к базе данных
    conn = await asyncpg.connect(str(settings.DATABASE_URL).replace('+asyncpg', ''))
    
    try:
        # Проверяем, существует ли колонка timezone
        has_timezone = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'timezone'"
        )
        
        if has_timezone > 0:
            print("Колонка timezone уже существует в таблице users")
            return
        
        # Добавляем колонку timezone
        await conn.execute(
            "ALTER TABLE users ADD COLUMN timezone VARCHAR(32) DEFAULT 'UTC+5'"
        )
        
        print("Колонка timezone успешно добавлена в таблицу users")
    except Exception as e:
        print(f"Ошибка при добавлении колонки timezone: {e}")
    finally:
        # Закрываем соединение
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_timezone_column())
