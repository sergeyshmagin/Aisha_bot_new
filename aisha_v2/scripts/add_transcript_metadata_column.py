"""
Скрипт для добавления недостающих колонок в таблицу user_transcripts
"""
import asyncio
import asyncpg
from aisha_v2.app.core.config import settings

async def add_columns():
    """Добавляет недостающие колонки в таблицу user_transcripts"""
    # Подключаемся к базе данных
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB
    )
    
    try:
        # Проверяем, существует ли колонка transcript_metadata
        transcript_metadata_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'user_transcripts' 
                AND column_name = 'transcript_metadata'
            )
            """
        )
        
        if not transcript_metadata_exists:
            # Добавляем колонку transcript_metadata
            await conn.execute(
                """
                ALTER TABLE user_transcripts 
                ADD COLUMN transcript_metadata JSONB DEFAULT '{}'::jsonb
                """
            )
            print("Колонка transcript_metadata успешно добавлена")
        else:
            print("Колонка transcript_metadata уже существует")
        
        # Проверяем, существует ли колонка updated_at
        updated_at_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'user_transcripts' 
                AND column_name = 'updated_at'
            )
            """
        )
        
        if not updated_at_exists:
            # Добавляем колонку updated_at
            await conn.execute(
                """
                ALTER TABLE user_transcripts 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                """
            )
            print("Колонка updated_at успешно добавлена")
        else:
            print("Колонка updated_at уже существует")
    finally:
        # Закрываем соединение
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_columns())
