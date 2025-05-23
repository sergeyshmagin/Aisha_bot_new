"""
Скрипт для обновления часового пояса пользователя
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.models import User
from app.core.config import settings

async def update_user_timezone():
    """Обновить часовой пояс пользователя"""
    # Создаем подключение к базе данных
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Открываем сессию
    async with async_session() as session:
        # Получаем всех пользователей
        from sqlalchemy import text
        result = await session.execute(text("SELECT * FROM users"))
        users = result.fetchall()
        
        # Обновляем часовой пояс для каждого пользователя
        for user in users:
            await session.execute(
                text("UPDATE users SET timezone = :timezone WHERE id = :id"),
                {"timezone": "UTC+5", "id": user[0]}  # Используем индекс для доступа к ID
            )
        
        # Сохраняем изменения
        await session.commit()
        
        print(f"Обновлен часовой пояс для {len(users)} пользователей")

if __name__ == "__main__":
    asyncio.run(update_user_timezone())
