#!/usr/bin/env python3
import asyncio
import logging
import os
import json
import aiofiles
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from minio import Minio
from dotenv import load_dotenv

from shared_storage import storage_utils
from frontend_bot.services.avatar_service import AvatarService
from frontend_bot.services.transcript_service import TranscriptService
from frontend_bot.services.history_service import HistoryService
from database.models import User, UserAvatar, UserTranscript, UserHistory
from frontend_bot.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем корень проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class DataMigrator:
    """Класс для миграции данных в MinIO."""
    
    def __init__(self):
        """Инициализация мигратора."""
        load_dotenv()
        
        # Настройки MinIO
        self.minio_client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
        
        # Настройки базы данных
        self.engine = create_async_engine(os.getenv("DATABASE_URL"))
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Настройки бакета
        self.bucket_name = os.getenv("MINIO_BUCKET", "user-data")
        self._ensure_bucket_exists()
        
        # Статистика миграции
        self.stats = {
            "avatars": {"total": 0, "success": 0, "failed": 0, "rollback": 0},
            "transcripts": {"total": 0, "success": 0, "failed": 0, "rollback": 0},
            "history": {"total": 0, "success": 0, "failed": 0, "rollback": 0}
        }
        
        # Для отката
        self.migrated_files: Dict[str, List[Dict[str, Any]]] = {
            "avatars": [],
            "transcripts": [],
            "history": []
        }
    
    def _ensure_bucket_exists(self):
        """Проверяет существование бакета и создает его при необходимости."""
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)
    
    async def migrate_user_data(self, user: User):
        """Мигрирует данные пользователя в MinIO.
        
        Args:
            user: Объект пользователя
        """
        # Миграция аватаров
        async with self.async_session() as session:
            avatars = await session.execute(
                select(UserAvatar).where(UserAvatar.user_id == user.id)
            )
            for avatar in avatars.scalars():
                await self._migrate_avatar(avatar)
            
            # Миграция транскриптов
            transcripts = await session.execute(
                select(UserTranscript).where(UserTranscript.user_id == user.id)
            )
            for transcript in transcripts.scalars():
                await self._migrate_transcript(transcript)
            
            # Миграция истории
            history = await session.execute(
                select(UserHistory).where(UserHistory.user_id == user.id)
            )
            for entry in history.scalars():
                await self._migrate_history(entry)
    
    async def _migrate_avatar(self, avatar: UserAvatar):
        """Мигрирует аватар в MinIO.
        
        Args:
            avatar: Объект аватара
        """
        if not avatar.file_path:
            return
        
        object_name = f"avatars/{avatar.user_id}/{os.path.basename(avatar.file_path)}"
        try:
            self.minio_client.fput_object(
                self.bucket_name,
                object_name,
                avatar.file_path
            )
            print(f"Migrated avatar: {object_name}")
        except Exception as e:
            print(f"Error migrating avatar {object_name}: {e}")
    
    async def _migrate_transcript(self, transcript: UserTranscript):
        """Мигрирует транскрипт в MinIO.
        
        Args:
            transcript: Объект транскрипта
        """
        if not transcript.file_path:
            return
        
        object_name = f"transcripts/{transcript.user_id}/{os.path.basename(transcript.file_path)}"
        try:
            self.minio_client.fput_object(
                self.bucket_name,
                object_name,
                transcript.file_path
            )
            print(f"Migrated transcript: {object_name}")
        except Exception as e:
            print(f"Error migrating transcript {object_name}: {e}")
    
    async def _migrate_history(self, history: UserHistory):
        """Мигрирует историю в MinIO.
        
        Args:
            history: Объект истории
        """
        if not history.file_path:
            return
        
        object_name = f"history/{history.user_id}/{os.path.basename(history.file_path)}"
        try:
            self.minio_client.fput_object(
                self.bucket_name,
                object_name,
                history.file_path
            )
            print(f"Migrated history: {object_name}")
        except Exception as e:
            print(f"Error migrating history {object_name}: {e}")
    
    async def init_storage(self):
        """Инициализация хранилища MinIO"""
        try:
            await storage_utils.init_storage()
            logger.info("MinIO storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO storage: {e}")
            raise
    
    async def migrate_avatars(self, batch_size: int = 100) -> None:
        """Миграция аватаров"""
        logger.info("Starting avatar migration...")
        
        # Получаем все аватары из старого хранилища
        query = select(UserAvatar)
        result = await self.async_session.execute(query)
        avatars = result.scalars().all()
        
        self.stats["avatars"]["total"] = len(avatars)
        
        for i in range(0, len(avatars), batch_size):
            batch = avatars[i:i + batch_size]
            for avatar in batch:
                try:
                    # Получаем данные из старого хранилища
                    old_photo_data = await self._get_old_avatar_data(avatar.photo_key)
                    old_preview_data = await self._get_old_avatar_data(avatar.preview_key)
                    
                    if not old_photo_data or not old_preview_data:
                        logger.warning(f"Missing data for avatar {avatar.id}")
                        self.stats["avatars"]["failed"] += 1
                        continue
                    
                    # Сохраняем в MinIO
                    new_avatar = await self.avatar_service.save_avatar(
                        user_id=avatar.user_id,
                        photo_data=old_photo_data,
                        preview_data=old_preview_data
                    )
                    
                    # Сохраняем информацию для отката
                    self.migrated_files["avatars"].append({
                        "id": avatar.id,
                        "photo_key": new_avatar.photo_key,
                        "preview_key": new_avatar.preview_key
                    })
                    
                    self.stats["avatars"]["success"] += 1
                    logger.info(f"Migrated avatar {avatar.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate avatar {avatar.id}: {e}")
                    self.stats["avatars"]["failed"] += 1
                    await self._rollback_avatar(avatar.id)
    
    async def migrate_transcripts(self, batch_size: int = 100) -> None:
        """Миграция транскриптов"""
        logger.info("Starting transcript migration...")
        
        # Получаем все транскрипты из старого хранилища
        query = select(UserTranscript)
        result = await self.async_session.execute(query)
        transcripts = result.scalars().all()
        
        self.stats["transcripts"]["total"] = len(transcripts)
        
        for i in range(0, len(transcripts), batch_size):
            batch = transcripts[i:i + batch_size]
            for transcript in batch:
                try:
                    # Получаем данные из старого хранилища
                    old_audio_data = await self._get_old_transcript_data(transcript.audio_key)
                    old_transcript_data = await self._get_old_transcript_data(transcript.transcript_key)
                    
                    if not old_audio_data or not old_transcript_data:
                        logger.warning(f"Missing data for transcript {transcript.id}")
                        self.stats["transcripts"]["failed"] += 1
                        continue
                    
                    # Сохраняем в MinIO
                    new_transcript = await self.transcript_service.save_transcript(
                        user_id=transcript.user_id,
                        audio_data=old_audio_data,
                        transcript_data=old_transcript_data
                    )
                    
                    # Сохраняем информацию для отката
                    self.migrated_files["transcripts"].append({
                        "id": transcript.id,
                        "audio_key": new_transcript.audio_key,
                        "transcript_key": new_transcript.transcript_key
                    })
                    
                    self.stats["transcripts"]["success"] += 1
                    logger.info(f"Migrated transcript {transcript.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate transcript {transcript.id}: {e}")
                    self.stats["transcripts"]["failed"] += 1
                    await self._rollback_transcript(transcript.id)
    
    async def migrate_history(self, batch_size: int = 100) -> None:
        """Миграция истории"""
        logger.info("Starting history migration...")
        
        # Получаем всю историю из старого хранилища
        query = select(UserHistory)
        result = await self.async_session.execute(query)
        history_entries = result.scalars().all()
        
        self.stats["history"]["total"] = len(history_entries)
        
        for i in range(0, len(history_entries), batch_size):
            batch = history_entries[i:i + batch_size]
            for history in batch:
                try:
                    # Получаем данные из старого хранилища
                    old_content = await self._get_old_history_data(history.content_key)
                    
                    if not old_content:
                        logger.warning(f"Missing data for history {history.id}")
                        self.stats["history"]["failed"] += 1
                        continue
                    
                    # Сохраняем в MinIO
                    new_history = await self.history_service.save_history(
                        user_id=history.user_id,
                        content=old_content
                    )
                    
                    # Сохраняем информацию для отката
                    self.migrated_files["history"].append({
                        "id": history.id,
                        "content_key": new_history.content_key
                    })
                    
                    self.stats["history"]["success"] += 1
                    logger.info(f"Migrated history {history.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate history {history.id}: {e}")
                    self.stats["history"]["failed"] += 1
                    await self._rollback_history(history.id)
    
    async def _get_old_avatar_data(self, key: str) -> Optional[bytes]:
        """Получение данных аватара из старого хранилища"""
        try:
            file_path = settings.AVATAR_STORAGE_PATH / key
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Failed to read avatar file {key}: {e}")
            return None
    
    async def _get_old_transcript_data(self, key: str) -> Optional[bytes]:
        """Получение данных транскрипта из старого хранилища"""
        try:
            file_path = settings.TRANSCRIPTS_PATH / key
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Failed to read transcript file {key}: {e}")
            return None
    
    async def _get_old_history_data(self, key: str) -> Optional[bytes]:
        """Получение данных истории из старого хранилища"""
        try:
            file_path = Path("storage/documents") / key
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Failed to read history file {key}: {e}")
            return None
    
    async def _rollback_avatar(self, avatar_id: str) -> None:
        """Откат миграции аватара"""
        try:
            for migrated in self.migrated_files["avatars"]:
                if migrated["id"] == avatar_id:
                    await storage_utils.delete_file("avatars", migrated["photo_key"])
                    await storage_utils.delete_file("avatars", migrated["preview_key"])
                    self.migrated_files["avatars"].remove(migrated)
                    self.stats["avatars"]["rollback"] += 1
                    logger.info(f"Rolled back avatar {avatar_id}")
                    break
        except Exception as e:
            logger.error(f"Failed to rollback avatar {avatar_id}: {e}")
    
    async def _rollback_transcript(self, transcript_id: str) -> None:
        """Откат миграции транскрипта"""
        try:
            for migrated in self.migrated_files["transcripts"]:
                if migrated["id"] == transcript_id:
                    await storage_utils.delete_file("transcripts", migrated["audio_key"])
                    await storage_utils.delete_file("transcripts", migrated["transcript_key"])
                    self.migrated_files["transcripts"].remove(migrated)
                    self.stats["transcripts"]["rollback"] += 1
                    logger.info(f"Rolled back transcript {transcript_id}")
                    break
        except Exception as e:
            logger.error(f"Failed to rollback transcript {transcript_id}: {e}")
    
    async def _rollback_history(self, history_id: str) -> None:
        """Откат миграции истории"""
        try:
            for migrated in self.migrated_files["history"]:
                if migrated["id"] == history_id:
                    await storage_utils.delete_file("documents", migrated["content_key"])
                    self.migrated_files["history"].remove(migrated)
                    self.stats["history"]["rollback"] += 1
                    logger.info(f"Rolled back history {history_id}")
                    break
        except Exception as e:
            logger.error(f"Failed to rollback history {history_id}: {e}")
    
    async def validate_migration(self) -> bool:
        """Валидация миграции"""
        logger.info("Validating migration...")
        
        success = True
        
        # Проверяем аватары
        for migrated in self.migrated_files["avatars"]:
            try:
                photo_data = await storage_utils.download_file("avatars", migrated["photo_key"])
                preview_data = await storage_utils.download_file("avatars", migrated["preview_key"])
                if not photo_data or not preview_data:
                    logger.error(f"Validation failed for avatar {migrated['id']}")
                    success = False
            except Exception as e:
                logger.error(f"Validation failed for avatar {migrated['id']}: {e}")
                success = False
        
        # Проверяем транскрипты
        for migrated in self.migrated_files["transcripts"]:
            try:
                audio_data = await storage_utils.download_file("transcripts", migrated["audio_key"])
                transcript_data = await storage_utils.download_file("transcripts", migrated["transcript_key"])
                if not audio_data or not transcript_data:
                    logger.error(f"Validation failed for transcript {migrated['id']}")
                    success = False
            except Exception as e:
                logger.error(f"Validation failed for transcript {migrated['id']}: {e}")
                success = False
        
        # Проверяем историю
        for migrated in self.migrated_files["history"]:
            try:
                content = await storage_utils.download_file("documents", migrated["content_key"])
                if not content:
                    logger.error(f"Validation failed for history {migrated['id']}")
                    success = False
            except Exception as e:
                logger.error(f"Validation failed for history {migrated['id']}: {e}")
                success = False
        
        if success:
            logger.info("Migration validation successful")
        else:
            logger.error("Migration validation failed")
        
        return success
    
    def print_stats(self):
        """Вывод статистики миграции"""
        logger.info("\nMigration Statistics:")
        for data_type, stats in self.stats.items():
            logger.info(f"\n{data_type.capitalize()}:")
            logger.info(f"  Total: {stats['total']}")
            logger.info(f"  Success: {stats['success']}")
            logger.info(f"  Failed: {stats['failed']}")
            logger.info(f"  Rollback: {stats['rollback']}")
            if stats['total'] > 0:
                success_rate = (stats['success'] / stats['total']) * 100
                logger.info(f"  Success Rate: {success_rate:.2f}%")

async def main():
    """Основная функция миграции"""
    logger.info("Starting data migration to MinIO...")
    
    migrator = DataMigrator()
    
    try:
        # Инициализация хранилища
        await migrator.init_storage()
        
        # Миграция данных
        await migrator.migrate_avatars()
        await migrator.migrate_transcripts()
        await migrator.migrate_history()
        
        # Валидация
        success = await migrator.validate_migration()
        
        # Вывод статистики
        migrator.print_stats()
        
        if not success:
            logger.error("Migration completed with validation errors")
            return 1
        
        logger.info("Migration completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

if __name__ == "__main__":
    asyncio.run(main()) 