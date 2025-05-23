"""
Скрипт для миграции данных из старой базы в новую
"""
import asyncio
import logging
from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.config import async_engine as new_engine
from app.database.models import Avatar, AvatarPhoto, User, UserBalance, UserState

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL для старой базы данных
OLD_DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"


async def get_old_data(session: AsyncSession) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Получить данные из старой базы"""
    # Получаем пользователей
    users = await session.execute(
        text("""
            SELECT id, telegram_id, first_name, last_name, username, 
                   language_code, is_premium, created_at, updated_at
            FROM users
        """)
    )
    users = [dict(row) for row in users]

    # Получаем аватары
    avatars = await session.execute(
        text("""
            SELECT id, user_id, name, gender, status, avatar_data, 
                   created_at, updated_at
            FROM avatars
        """)
    )
    avatars = [dict(row) for row in avatars]

    # Получаем фото аватаров
    photos = await session.execute(
        text("""
            SELECT id, avatar_id, minio_key, "order", 
                   created_at, updated_at
            FROM avatar_photos
        """)
    )
    photos = [dict(row) for row in photos]

    return users, avatars, photos


async def migrate_data():
    """Миграция данных из старой базы в новую"""
    try:
        async with AsyncSession(new_engine) as session:
            # Получаем данные из старой базы
            users, avatars, photos = await get_old_data(session)
            logger.info(f"Found {len(users)} users, {len(avatars)} avatars, {len(photos)} photos")

            # Мигрируем пользователей
            for user_data in users:
                user = User(
                    id=user_data["id"],
                    telegram_id=user_data["telegram_id"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    username=user_data["username"],
                    language_code=user_data["language_code"],
                    is_premium=user_data["is_premium"],
                )
                session.add(user)
                
                # Создаем баланс
                balance = UserBalance(user_id=user.id, coins=0.0)
                session.add(balance)

            await session.flush()
            logger.info("Users migrated successfully")

            # Мигрируем аватары
            for avatar_data in avatars:
                avatar = Avatar(
                    id=avatar_data["id"],
                    user_id=avatar_data["user_id"],
                    name=avatar_data["name"],
                    gender=avatar_data["gender"],
                    status=avatar_data["status"],
                    is_draft=avatar_data["status"] == "draft",
                    avatar_data=avatar_data["avatar_data"],
                )
                session.add(avatar)

            await session.flush()
            logger.info("Avatars migrated successfully")

            # Мигрируем фото
            for photo_data in photos:
                photo = AvatarPhoto(
                    id=photo_data["id"],
                    avatar_id=photo_data["avatar_id"],
                    minio_key=photo_data["minio_key"],
                    order=photo_data["order"],
                )
                session.add(photo)

            await session.flush()
            logger.info("Photos migrated successfully")

            # Сохраняем все изменения
            await session.commit()
            logger.info("Data migration completed successfully")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_data())
