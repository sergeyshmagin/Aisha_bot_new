"""
Сервис для работы с аватарами пользователей.
Хранит файлы в MinIO и метаданные в PostgreSQL.
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from PIL import Image
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from frontend_bot.services.minio_client import upload_file, download_file, delete_file, generate_presigned_url, check_file_exists
from database.models import UserAvatar
from frontend_bot.config import settings

class AvatarService:
    """Сервис для работы с аватарами пользователей"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bucket = settings.AVATAR_DIR
        
    async def init(self):
        """Инициализирует хранилище"""
        await init_storage()
        
    async def validate_photo(self, photo_data: bytes) -> bool:
        """
        Проверяет фото на соответствие требованиям:
        - Размер не более MAX_PHOTO_SIZE
        - Формат из ALLOWED_PHOTO_FORMATS
        - Разрешение не более PHOTO_MIN_RES
        
        Args:
            photo_data (bytes): Данные фото
            
        Returns:
            bool: True если фото валидно
        """
        try:
            # Проверка размера
            if len(photo_data) > settings.PHOTO_MAX_MB * 1024 * 1024:
                return False
                
            # Проверка формата и разрешения
            img = Image.open(io.BytesIO(photo_data))
            if img.format.lower() not in settings.ALLOWED_PHOTO_FORMATS:
                return False
            if max(img.size) > settings.PHOTO_MIN_RES:
                return False
                
            return True
        except Exception:
            return False
            
    async def generate_preview(self, photo_data: bytes) -> bytes:
        """
        Генерирует превью фото размером THUMBNAIL_SIZE x THUMBNAIL_SIZE.
        
        Args:
            photo_data (bytes): Данные оригинального фото
            
        Returns:
            bytes: Данные превью
        """
        img = Image.open(io.BytesIO(photo_data))
        img.thumbnail((settings.THUMBNAIL_SIZE, settings.THUMBNAIL_SIZE))
        buffer = io.BytesIO()
        img.save(buffer, format=img.format)
        return buffer.getvalue()
        
    async def save_avatar(
        self,
        user_id: int,
        photo_data: bytes,
        preview_data: bytes,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Сохраняет аватар пользователя.
        
        Args:
            user_id (int): ID пользователя
            photo_data (bytes): Данные фото
            preview_data (bytes): Данные превью
            description (str, optional): Описание аватара
            
        Returns:
            Dict[str, Any]: Метаданные сохраненного аватара
            
        Raises:
            ValueError: Если фото не прошло валидацию
        """
        if not await self.validate_photo(photo_data):
            raise ValueError("Invalid photo")
            
        # Генерируем уникальные ключи для файлов
        photo_key = f"{user_id}/{uuid.uuid4()}/photo.jpg"
        preview_key = f"{user_id}/{uuid.uuid4()}/preview.jpg"
        
        # Загружаем файлы в MinIO
        await upload_file(
            self.bucket,
            photo_key,
            photo_data,
            content_type="image/jpeg"
        )
        await upload_file(
            self.bucket,
            preview_key,
            preview_data,
            content_type="image/jpeg"
        )
        
        # Сохраняем метаданные в БД
        avatar = UserAvatar(
            user_id=user_id,
            photo_key=photo_key,
            preview_key=preview_key,
            created_at=datetime.utcnow()
        )
        self.session.add(avatar)
        await self.session.commit()
        
        return {
            "id": avatar.id,
            "photo_url": f"/{self.bucket}/{photo_key}",
            "preview_url": f"/{self.bucket}/{preview_key}",
            "created_at": avatar.created_at
        }
        
    async def get_avatar(self, user_id: int, avatar_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает аватар пользователя.
        
        Args:
            user_id (int): ID пользователя
            avatar_id (int): ID аватара
            
        Returns:
            Optional[Dict[str, Any]]: Метаданные аватара или None если не найден
        """
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.id == avatar_id
        )
        result = await self.session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            return None
            
        # Получаем presigned URL для файлов
        photo_url = await generate_presigned_url(self.bucket, avatar.photo_key)
        preview_url = await generate_presigned_url(self.bucket, avatar.preview_key)
        
        return {
            "id": avatar.id,
            "photo_url": photo_url,
            "preview_url": preview_url,
            "created_at": avatar.created_at
        }
        
    async def delete_avatar(self, user_id: int, avatar_id: int) -> bool:
        """
        Удаляет аватар пользователя.
        
        Args:
            user_id (int): ID пользователя
            avatar_id (int): ID аватара
            
        Returns:
            bool: True если аватар был удален
        """
        # Получаем метаданные аватара
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.id == avatar_id
        )
        result = await self.session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            return False
            
        # Удаляем файлы из MinIO
        await delete_file(self.bucket, avatar.photo_key)
        await delete_file(self.bucket, avatar.preview_key)
        
        # Удаляем запись из БД
        await self.session.delete(avatar)
        await self.session.commit()
        
        return True
        
    async def list_avatars(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получает список аватаров пользователя.
        
        Args:
            user_id (int): ID пользователя
            limit (int): Максимальное количество аватаров
            offset (int): Смещение
            
        Returns:
            List[Dict[str, Any]]: Список метаданных аватаров
        """
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id
        ).order_by(
            UserAvatar.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        avatars = result.scalars().all()
        
        return [{
            "id": avatar.id,
            "photo_url": f"/{self.bucket}/{avatar.photo_key}",
            "preview_url": f"/{self.bucket}/{avatar.preview_key}",
            "created_at": avatar.created_at
        } for avatar in avatars] 