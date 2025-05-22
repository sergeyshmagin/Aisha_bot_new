"""
Сервис для работы с транскриптами.
Хранит файлы в MinIO и метаданные в PostgreSQL.
"""

import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database.models import UserTranscript, UserTranscriptCache
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.minio_client import upload_file, download_file, delete_file, generate_presigned_url, check_file_exists

logger = get_logger(__name__)

class TranscriptService:
    """Сервис для работы с транскриптами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bucket = "transcripts"
        
    async def init(self):
        """Инициализирует хранилище"""
        # await init_storage()
        
    async def save_transcript(
        self,
        user_id: int,
        audio_data: bytes,
        transcript_data: bytes,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Сохраняет транскрипт.
        
        Args:
            user_id (int): ID пользователя
            audio_data (bytes): Данные аудио
            transcript_data (bytes): Данные транскрипта
            metadata (Dict[str, Any], optional): Дополнительные метаданные
            
        Returns:
            Dict[str, Any]: Метаданные сохраненного транскрипта
        """
        # Генерируем уникальные ключи для файлов
        audio_key = f"{user_id}/{uuid.uuid4()}/audio.mp3"
        transcript_key = f"{user_id}/{uuid.uuid4()}/transcript.txt"
        
        # Загружаем файлы в MinIO
        await upload_file(
            self.bucket,
            audio_key,
            audio_data,
            content_type="audio/mpeg"
        )
        await upload_file(
            self.bucket,
            transcript_key,
            transcript_data,
            content_type="text/plain"
        )
        
        # Сохраняем метаданные в БД
        transcript = UserTranscript(
            user_id=user_id,
            audio_key=audio_key,
            transcript_key=transcript_key,
            created_at=datetime.utcnow()
        )
        self.session.add(transcript)
        await self.session.commit()
        
        # Обновляем кэш
        cache = UserTranscriptCache(
            user_id=user_id,
            path=transcript_key
        )
        self.session.add(cache)
        await self.session.commit()
        
        return {
            "id": transcript.id,
            "audio_url": f"/{self.bucket}/{audio_key}",
            "transcript_url": f"/{self.bucket}/{transcript_key}",
            "created_at": transcript.created_at
        }
        
    async def get_transcript(self, user_id: int, transcript_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает транскрипт.
        
        Args:
            user_id (int): ID пользователя
            transcript_id (int): ID транскрипта
            
        Returns:
            Optional[Dict[str, Any]]: Метаданные транскрипта или None если не найден
        """
        query = select(UserTranscript).where(
            UserTranscript.user_id == user_id,
            UserTranscript.id == transcript_id
        )
        result = await self.session.execute(query)
        transcript = result.scalar_one_or_none()
        
        if not transcript:
            return None
            
        # Получаем presigned URL для файлов
        audio_url = await generate_presigned_url(self.bucket, transcript.audio_key)
        transcript_url = await generate_presigned_url(self.bucket, transcript.transcript_key)
        
        return {
            "id": transcript.id,
            "audio_url": audio_url,
            "transcript_url": transcript_url,
            "created_at": transcript.created_at
        }
        
    async def delete_transcript(self, user_id: int, transcript_id: int) -> bool:
        """
        Удаляет транскрипт.
        
        Args:
            user_id (int): ID пользователя
            transcript_id (int): ID транскрипта
            
        Returns:
            bool: True если транскрипт был удален
        """
        # Получаем метаданные транскрипта
        query = select(UserTranscript).where(
            UserTranscript.user_id == user_id,
            UserTranscript.id == transcript_id
        )
        result = await self.session.execute(query)
        transcript = result.scalar_one_or_none()
        
        if not transcript:
            return False
            
        # Удаляем файлы из MinIO
        await delete_file(self.bucket, transcript.audio_key)
        await delete_file(self.bucket, transcript.transcript_key)
        
        # Удаляем запись из БД
        await self.session.delete(transcript)
        await self.session.commit()
        
        return True
        
    async def list_transcripts(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Получает список транскриптов пользователя.
        
        Args:
            user_id (int): ID пользователя
            limit (int): Максимальное количество транскриптов
            offset (int): Смещение
            
        Returns:
            List[Dict[str, Any]]: Список метаданных транскриптов
        """
        query = select(UserTranscript).where(
            UserTranscript.user_id == user_id
        ).order_by(
            UserTranscript.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        transcripts = result.scalars().all()
        
        return [{
            "id": transcript.id,
            "audio_url": f"/{self.bucket}/{transcript.audio_key}",
            "transcript_url": f"/{self.bucket}/{transcript.transcript_key}",
            "created_at": transcript.created_at
        } for transcript in transcripts]

    async def get_transcript_path(self, user_id: int) -> Optional[str]:
        """
        Получает путь к последнему транскрипту пользователя.
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            Optional[str]: Путь к транскрипту или None
        """
        query = select(UserTranscriptCache).where(
            UserTranscriptCache.user_id == user_id
        )
        result = await self.session.execute(query)
        cache = result.scalar_one_or_none()
        return cache.path if cache else None

    async def clear_transcript_cache(self, user_id: int) -> None:
        """
        Очищает кэш транскриптов пользователя.
        
        Args:
            user_id (int): ID пользователя
        """
        query = delete(UserTranscriptCache).where(
            UserTranscriptCache.user_id == user_id
        )
        await self.session.execute(query)
        await self.session.commit()

async def get_user_transcript_or_error(
    user_id: int,
    transcript_id: int,
    session: AsyncSession
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Получает транскрипт пользователя или возвращает ошибку.
    
    Args:
        user_id (int): ID пользователя
        transcript_id (int): ID транскрипта
        session (AsyncSession): Сессия SQLAlchemy
        
    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]: (транскрипт, ошибка)
    """
    service = TranscriptService(session)
    await service.init()
    
    transcript = await service.get_transcript(user_id, transcript_id)
    if not transcript:
        return None, "Транскрипт не найден"
        
    return transcript, None

async def send_document_with_caption(
    bot: AsyncTeleBot,
    chat_id: int,
    file_path: str,
    caption: str
) -> None:
    """
    Отправляет документ с подписью.
    
    Args:
        bot (AsyncTeleBot): Экземпляр бота
        chat_id (int): ID чата
        file_path (str): Путь к файлу
        caption (str): Подпись
    """
    with open(file_path, "rb") as f:
        await bot.send_document(
            chat_id,
            f,
            caption=caption
        )

async def send_transcript_error(
    bot: AsyncTeleBot,
    chat_id: int,
    error: str
) -> None:
    """
    Отправляет сообщение об ошибке транскрипта.
    
    Args:
        bot (AsyncTeleBot): Экземпляр бота
        chat_id (int): ID чата
        error (str): Текст ошибки
    """
    try:
        await bot.send_message(
            chat_id,
            f"❌ Ошибка при обработке транскрипта: {error}"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")
        raise 