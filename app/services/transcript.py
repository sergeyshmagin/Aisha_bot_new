"""
Сервис для работы с транскриптами (async MinIO)
"""
import io
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

from app.core.config import settings
from app.database.models import UserTranscript
from app.database.repositories import TranscriptRepository
from app.services.base import BaseService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

def _normalize_user_id(user_id: Union[int, str, UUID]) -> Union[str, UUID]:
    """Нормализует user_id в зависимости от того, что ожидает репозиторий"""
    if isinstance(user_id, UUID):
        return user_id
    elif isinstance(user_id, str):
        # Пытаемся преобразовать в UUID если это строка UUID
        try:
            return UUID(user_id)
        except ValueError:
            return user_id
    else:
        # Если это int, преобразуем в строку
        return str(user_id)

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
        user_id: Union[int, str, UUID],
        audio_data: Optional[bytes] = None,
        transcript_data: bytes = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Сохраняет транскрипт в MinIO и БД (асинхронно)
        """
        normalized_user_id = _normalize_user_id(user_id)
        logger.info(f"[SAVE] Начало сохранения транскрипта для user_id={normalized_user_id}")
        
        if not transcript_data:
            logger.error("[SAVE] transcript_data отсутствует")
            return None
            
        transcript = await self.transcript_repo.create({
            "user_id": normalized_user_id,
            "transcript_metadata": metadata or {}
        })
        transcript_id = transcript.id
        logger.info(f"[SAVE] Создана запись в БД: transcript_id={transcript_id}")
        
        storage = StorageService()
        # Сохраняем аудио, если есть
        if audio_data:
            audio_key = f"{normalized_user_id}/{transcript_id}/audio.mp3"
            logger.info(f"[SAVE] Сохранение аудио: {audio_key}")
            success = await storage.upload_file(
                bucket=self.bucket,
                object_name=audio_key,
                data=audio_data,
                content_type="audio/mpeg"
            )
            if not success:
                logger.error(f"[SAVE] Ошибка сохранения аудио: {audio_key}")
                return None
                
            await self.transcript_repo.update(
                transcript_id, {"audio_key": audio_key}
            )
            logger.info(f"[SAVE] Аудио сохранено: {audio_key}")
            
        # Сохраняем текст транскрипта
        transcript_key = f"{normalized_user_id}/{transcript_id}/transcript.txt"
        logger.info(f"[SAVE] Сохранение транскрипта: {transcript_key}")
        success = await storage.upload_file(
            bucket=self.bucket,
            object_name=transcript_key,
            data=transcript_data,
            content_type="text/plain"
        )
        if not success:
            logger.error(f"[SAVE] Ошибка сохранения транскрипта: {transcript_key}")
            return None
            
        await self.transcript_repo.update(
            transcript_id, {"transcript_key": transcript_key}
        )
        logger.info(f"[SAVE] Транскрипт сохранен: {transcript_key}")
        
        # Получаем актуальный объект из БД
        transcript = await self.transcript_repo.get_transcript_by_id(normalized_user_id, transcript_id)
        logger.info(f"[SAVE] Возвращаю актуальный transcript: id={transcript.id}, transcript_key={transcript.transcript_key}")
        
        return {
            "id": str(transcript.id),
            "audio_key": transcript.audio_key,
            "transcript_key": transcript.transcript_key,
            "created_at": transcript.created_at,
            "metadata": transcript.transcript_metadata
        }

    async def get_transcript(
        self,
        user_id: Union[int, str, UUID],
        transcript_id: UUID
    ) -> Optional[Dict]:
        """
        Получает транскрипт по ID (с presigned URL)
        """
        normalized_user_id = _normalize_user_id(user_id)
        transcript = await self.transcript_repo.get_transcript_by_id(normalized_user_id, transcript_id)
        if not transcript:
            return None
        expires = settings.MINIO_PRESIGNED_EXPIRES or 3600
        storage = StorageService()
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

    # =================== LEGACY CODE - ЗАКОММЕНТИРОВАН ===================    # LEGACY: Устаревший метод для обратной совместимости    # TODO: Удалить после полной миграции на list_transcripts    # async def get_user_transcripts(self, user_id: Union[int, str, UUID]) -> List[Dict]:    #     """    #     LEGACY: Получает все транскрипты пользователя из БД (без MinIO)    #         #     Deprecated:    #         Используйте list_transcripts вместо этого метода    #     """    #     return await self.list_transcripts(user_id, limit=1000, offset=0)    # =================== END LEGACY CODE ===================

    async def list_transcripts(self, user_id: Union[int, str, UUID], limit: int = 10, offset: int = 0) -> List[dict]:
        """
        Получает список транскриптов пользователя с использованием MinIO для хранения
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество транскриптов
            offset: Смещение для пагинации
            
        Returns:
            Список словарей с данными транскриптов
        """
        logger.info(f"[LIST_TRANSCRIPTS] Начало: user_id={user_id}, limit={limit}, offset={offset}")
        
        try:
            # Используем репозиторий для получения данных
            raw_transcripts = await self.transcript_repo.get_user_transcripts(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            logger.info(f"[LIST_TRANSCRIPTS] Получено {len(raw_transcripts)} транскриптов из репозитория")
            
            # Конвертируем SQLAlchemy объекты в словари
            result = []
            for i, transcript in enumerate(raw_transcripts):
                logger.info(f"[LIST_TRANSCRIPTS] Обработка транскрипта {i}: id={transcript.id}, type={type(transcript)}")
                
                # Безопасная конвертация атрибутов 
                id_attr = getattr(transcript, 'id', None)
                user_id_attr = getattr(transcript, 'user_id', None)
                created_at_attr = getattr(transcript, 'created_at', None)
                metadata_attr = getattr(transcript, 'transcript_metadata', None)
                
                logger.info(f"[LIST_TRANSCRIPTS] Атрибуты извлечены: id={id_attr}, user_id={user_id_attr}")
                
                transcript_dict = {
                    "id": str(id_attr) if id_attr else None,
                    "created_at": created_at_attr.isoformat() if created_at_attr else None,
                    "metadata": metadata_attr or {}
                }
                
                logger.info(f"[LIST_TRANSCRIPTS] Создан dict для транскрипта {i}: keys={list(transcript_dict.keys())}")
                result.append(transcript_dict)
            
            logger.info(f"[LIST_TRANSCRIPTS] Завершено успешно, результат: {len(result)} элементов")
            return result
            
        except Exception as e:
            logger.error(f"[LIST_TRANSCRIPTS] Ошибка: {e}")
            raise

    async def delete_transcript(self, user_id: Union[int, str, UUID], transcript_id: UUID) -> bool:
        """Удаляет транскрипт (и файлы из MinIO)"""
        normalized_user_id = _normalize_user_id(user_id)
        transcript = await self.transcript_repo.get_transcript_by_id(normalized_user_id, transcript_id)
        if not transcript:
            return False
        storage = StorageService()
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

    async def get_transcript_content(self, user_id: Union[int, str, UUID], transcript_id: UUID) -> Optional[bytes]:
        """Получает содержимое транскрипта из MinIO"""
        normalized_user_id = _normalize_user_id(user_id)
        logger.info(f"[GET_CONTENT] START: user_id={normalized_user_id}, transcript_id={transcript_id}")
        try:
            transcript = await self.transcript_repo.get_transcript_by_id(normalized_user_id, transcript_id)
            logger.info(f"[GET_CONTENT] После get_transcript_by_id: transcript найден={transcript is not None}")
            if not transcript:
                logger.error(f"[GET_CONTENT] Транскрипт не найден в БД: user_id={normalized_user_id}, transcript_id={transcript_id}")
                return None
            logger.info(f"[GET_CONTENT] transcript.transcript_key={transcript.transcript_key}")
            storage = StorageService()
            if not transcript.transcript_key:
                logger.error(f"[GET_CONTENT] transcript_key отсутствует для transcript_id={transcript_id}")
                return None
            try:
                logger.info(f"[GET_CONTENT] Проверка существования файла в MinIO: bucket={self.bucket}, key={transcript.transcript_key}")
                import asyncio
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: storage.client.stat_object(self.bucket, transcript.transcript_key))
                logger.info(f"[GET_CONTENT] Файл существует в MinIO")
            except Exception as e:
                logger.error(f"[GET_CONTENT] Файл не найден в MinIO: {e}")
                return None
            logger.info(f"[GET_CONTENT] Загрузка файла из MinIO")
            content = await storage.download_file(self.bucket, transcript.transcript_key)
            logger.info(f"[GET_CONTENT] Файл загружен, размер={len(content) if content else 0} байт")
            if not content:
                logger.error(f"[GET_CONTENT] Получен пустой контент для transcript_id={transcript_id}")
                return None
            return content
        except Exception as e:
            logger.exception(f"[GET_CONTENT] Ошибка при получении содержимого транскрипта: {e}")
            return None

    async def get_all_transcripts(self, user_id: Union[int, str, UUID]) -> List[dict]:
        """
        Получает все транскрипты пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список всех транскриптов пользователя
        """
        return await self.list_transcripts(user_id, limit=1000, offset=0)
