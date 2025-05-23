"""
Скрипт для сброса и повторного создания таблицы user_transcripts
"""
import asyncio
import asyncpg
from app.core.config import settings

async def reset_table():
    """Сбрасывает и повторно создает таблицу user_transcripts"""
    # Подключаемся к базе данных
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB
    )
    
    try:
        # Проверяем, существует ли таблица
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name = 'user_transcripts'
            )
            """
        )
        
        if table_exists:
            # Удаляем таблицу
            await conn.execute("DROP TABLE user_transcripts")
            print("Таблица user_transcripts удалена")
        
        # Создаем таблицу заново
        await conn.execute("""
            CREATE TABLE user_transcripts (
                id UUID PRIMARY KEY,
                user_id UUID REFERENCES users(id),
                audio_key VARCHAR(255) NULL,
                transcript_key VARCHAR(255) NULL,
                transcript_metadata JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        print("Таблица user_transcripts успешно создана заново")
    finally:
        # Закрываем соединение
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_table())
