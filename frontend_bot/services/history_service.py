"""
Сервис для работы с историей пользователя.
Хранит файлы в MinIO и метаданные в PostgreSQL.
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from shared_storage.storage_utils import (
    init_storage,
    upload_file,
    download_file,
    delete_file,
    generate_presigned_url,
    get_file_metadata
)
from database.models import UserHistory
from frontend_bot.config import settings

class HistoryService:
    """Сервис для работы с историей пользователя"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bucket = "documents"
        
    async def init(self):
        """Инициализирует хранилище"""
        await init_storage()
        
    async def save_history(
        self,
        user_id: int,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Сохраняет запись в истории.
        
        Args:
            user_id (int): ID пользователя
            content (bytes): Содержимое записи
            metadata (Dict[str, Any], optional): Дополнительные метаданные
            
        Returns:
            Dict[str, Any]: Метаданные сохраненной записи
        """
        # Генерируем уникальный ключ для файла
        content_key = f"{user_id}/{uuid.uuid4()}/content.txt"
        
        # Загружаем файл в MinIO
        await upload_file(
            self.bucket,
            content_key,
            content,
            content_type="text/plain"
        )
        
        # Сохраняем метаданные в БД
        history = UserHistory(
            user_id=user_id,
            content_key=content_key,
            created_at=datetime.utcnow()
        )
        self.session.add(history)
        await self.session.commit()
        
        return {
            "id": history.id,
            "content_url": f"/{self.bucket}/{content_key}",
            "created_at": history.created_at
        }
        
    async def get_history(self, user_id: int, history_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает запись из истории.
        
        Args:
            user_id (int): ID пользователя
            history_id (int): ID записи
            
        Returns:
            Optional[Dict[str, Any]]: Метаданные записи или None если не найдена
        """
        query = select(UserHistory).where(
            UserHistory.user_id == user_id,
            UserHistory.id == history_id
        )
        result = await self.session.execute(query)
        history = result.scalar_one_or_none()
        
        if not history:
            return None
            
        # Получаем presigned URL для файла
        content_url = await generate_presigned_url(self.bucket, history.content_key)
        
        return {
            "id": history.id,
            "content_url": content_url,
            "created_at": history.created_at
        }
        
    async def delete_history(self, user_id: int, history_id: int) -> bool:
        """
        Удаляет запись из истории.
        
        Args:
            user_id (int): ID пользователя
            history_id (int): ID записи
            
        Returns:
            bool: True если запись была удалена
        """
        # Получаем метаданные записи
        query = select(UserHistory).where(
            UserHistory.user_id == user_id,
            UserHistory.id == history_id
        )
        result = await self.session.execute(query)
        history = result.scalar_one_or_none()
        
        if not history:
            return False
            
        # Удаляем файл из MinIO
        await delete_file(self.bucket, history.content_key)
        
        # Удаляем запись из БД
        await self.session.delete(history)
        await self.session.commit()
        
        return True
        
    async def list_history(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получает список записей из истории пользователя.
        
        Args:
            user_id (int): ID пользователя
            limit (int): Максимальное количество записей
            offset (int): Смещение
            
        Returns:
            List[Dict[str, Any]]: Список метаданных записей
        """
        query = select(UserHistory).where(
            UserHistory.user_id == user_id
        ).order_by(
            UserHistory.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        history_list = result.scalars().all()
        
        return [{
            "id": history.id,
            "content_url": f"/{self.bucket}/{history.content_key}",
            "created_at": history.created_at
        } for history in history_list]

    async def add_entry(
        self,
        session: AsyncSession,
        user_id: str,
        entry_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Добавляет запись в историю пользователя.
        
        Args:
            session (AsyncSession): Сессия SQLAlchemy
            user_id (str): ID пользователя
            entry_type (str): Тип записи
            metadata (Dict[str, Any]): Метаданные записи
            
        Returns:
            Dict[str, Any]: Метаданные сохраненной записи
        """
        await self.init()
        return await self.save_history(
            user_id=user_id,
            content=metadata.get("content", "").encode(),
            metadata={"type": entry_type, **metadata}
        )

async def add_history_entry(
    user_id: int,
    content: str,
    session: AsyncSession,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Добавляет запись в историю пользователя.
    
    Args:
        user_id (int): ID пользователя
        content (str): Содержимое записи
        session (AsyncSession): Сессия SQLAlchemy
        metadata (Dict[str, Any], optional): Дополнительные метаданные
        
    Returns:
        Dict[str, Any]: Метаданные сохраненной записи
    """
    service = HistoryService(session)
    await service.init()
    return await service.save_history(user_id, content.encode(), metadata) 