"""
Сервис для работы с транскриптами (async MinIO)
"""
import io
import logging
from datetime import timedelta
from typing import Dict, List, Optional
from uuid import UUID

from aisha_v2.app.core.config import settings
from aisha_v2.app.database.models import UserTranscript
from aisha_v2.app.database.repositories import TranscriptRepository
from aisha_v2.app.services.base import BaseService
from aisha_v2.app.services.storage import StorageService

logger = logging.getLogger(__name__)

class TranscriptService(BaseService):
    """
    Сервис для работы с транскриптами (асинхронный StorageService)
    """

    def _setup_repositories(self):
        """Инициализация репозиториев"""
        self.transcript_repo = TranscriptRepository(self.session)
        self.bucket = settings.MINIO_BUCKETS.get("transcripts", "transcripts")

    async def save_transcript(
        self,
        user_id: int,
        audio_data: Optional[bytes] = None,
        transcript_data: bytes = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Сохраняет транскрипт в MinIO и БД (асинхронно)
        """
        transcript = await self.transcript_repo.create({
            "user_id": user_id,
            "transcript_metadata": metadata or {}
        })
        transcript_id = transcript.id
        audio_key = None
        async with StorageService() as storage:
            # Сохраняем аудио, если есть
            if audio_data:
                audio_key = f"{user_id}/{transcript_id}/audio.mp3"
                await storage.upload_file(
                    bucket=self.bucket,
                    file_path=None,
                    user_id=user_id,
                    object_name=audio_key,
                    data=audio_data,
                    content_type="audio/mpeg"
                )
                transcript = await self.transcript_repo.update(
                    transcript_id, {"audio_key": audio_key}
                )
            # Сохраняем текст транскрипта
            transcript_key = f"{user_id}/{transcript_id}/transcript.txt"
            await storage.upload_file(
                bucket=self.bucket,
                file_path=None,
                user_id=user_id,
                object_name=transcript_key,
                data=transcript_data,
                content_type="text/plain"
            )
            transcript = await self.transcript_repo.update(
                transcript_id, {"transcript_key": transcript_key}
            )
        return {
            "id": str(transcript.id),
            "audio_key": transcript.audio_key,
            "transcript_key": transcript.transcript_key,
            "created_at": transcript.created_at,
            "metadata": transcript.transcript_metadata
        }

    async def get_transcript(
        self,
        user_id: int,
        transcript_id: UUID
    ) -> Optional[Dict]:
        """
        Получает транскрипт по ID (с presigned URL)
        """
        transcript = await self.transcript_repo.get_transcript_by_id(user_id, transcript_id)
        if not transcript:
            return None
        expires = settings.MINIO_PRESIGNED_EXPIRES or 3600
        async with StorageService() as storage:
            audio_url = None
            if transcript.audio_key:
                audio_url = await storage.generate_presigned_url(
                    bucket=self.bucket,
                    object_name=transcript.audio_key,
                    expires=expires
                )
            transcript_url = await storage.generate_presigned_url(
                bucket=self.bucket,
                object_name=transcript.transcript_key,
                expires=expires
            )
        created_at_str = None
        if transcript.created_at:
            try:
                created_at_str = transcript.created_at.isoformat()
            except Exception as e:
                logger.error(f"Error converting created_at to ISO format: {e}, type: {type(transcript.created_at)}, value: {transcript.created_at}")
                created_at_str = str(transcript.created_at)
        return {
            "id": str(transcript.id),
            "audio_url": audio_url,
            "transcript_url": transcript_url,
            "created_at": created_at_str,
            "metadata": transcript.transcript_metadata
        }

    async def get_user_transcripts(self, user_id: int) -> List[Dict]:
        """Получает все транскрипты пользователя без пагинации"""
        return await self.list_transcripts(user_id, limit=1000, offset=0)

    async def list_transcripts(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[Dict]:
        """Получает список транскриптов пользователя"""
        transcripts = await self.transcript_repo.get_user_transcripts(
            user_id, limit, offset
        )
        result = []
        for transcript in transcripts:
            created_at_str = None
            if transcript.created_at:
                try:
                    created_at_str = transcript.created_at.isoformat()
                except Exception as e:
                    logger.error(f"Error converting created_at to ISO format in list_transcripts: {e}, type: {type(transcript.created_at)}, value: {transcript.created_at}")
                    created_at_str = str(transcript.created_at)
            result.append({
                "id": str(transcript.id),
                "created_at": created_at_str,
                "metadata": transcript.transcript_metadata
            })
        return result

    async def delete_transcript(self, user_id: int, transcript_id: UUID) -> bool:
        """Удаляет транскрипт (и файлы из MinIO)"""
        transcript = await self.transcript_repo.get_transcript_by_id(user_id, transcript_id)
        if not transcript:
            return False
        async with StorageService() as storage:
            if transcript.audio_key:
                try:
                    await storage.delete_file(self.bucket, transcript.audio_key)
                except Exception as e:
                    logger.exception(f"Ошибка при удалении аудио из MinIO: {e}")
            try:
                await storage.delete_file(self.bucket, transcript.transcript_key)
            except Exception as e:
                logger.exception(f"Ошибка при удалении транскрипта из MinIO: {e}")
        return await self.transcript_repo.delete(transcript_id)

    async def get_transcript_content(self, user_id: int, transcript_id: UUID) -> Optional[bytes]:
        """Получает содержимое транскрипта из MinIO"""
        transcript = await self.transcript_repo.get_transcript_by_id(user_id, transcript_id)
        if not transcript:
            return None
        async with StorageService() as storage:
            try:
                content = await storage.download_file(self.bucket, transcript.transcript_key)
                return content
            except Exception as e:
                logger.exception(f"Ошибка при получении содержимого транскрипта: {e}")
                return None
