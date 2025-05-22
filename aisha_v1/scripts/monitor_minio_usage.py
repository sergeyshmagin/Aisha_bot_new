#!/usr/bin/env python3
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared_storage import storage_utils
from database.config import AsyncSessionLocal
from models.user import UserAvatar, UserTranscript, UserHistory

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinIOUsageMonitor:
    def __init__(self):
        self.stats = {
            "total_size": 0,
            "buckets": {},
            "users": {},
            "types": {
                "avatars": {"count": 0, "size": 0},
                "transcripts": {"count": 0, "size": 0},
                "history": {"count": 0, "size": 0}
            }
        }
    
    async def collect_stats(self):
        """Сбор статистики использования MinIO"""
        logger.info("Collecting MinIO usage statistics...")
        
        # Получаем статистику по bucket'ам
        for bucket in ["avatars", "transcripts", "documents", "temp"]:
            try:
                objects = await storage_utils.list_files(bucket)
                bucket_stats = {
                    "count": len(objects),
                    "size": 0
                }
                
                for obj in objects:
                    metadata = await storage_utils.get_file_metadata(bucket, obj)
                    bucket_stats["size"] += metadata["size"]
                
                self.stats["buckets"][bucket] = bucket_stats
                self.stats["total_size"] += bucket_stats["size"]
                
            except Exception as e:
                logger.error(f"Failed to get stats for bucket {bucket}: {e}")
        
        # Получаем статистику по пользователям
        async with AsyncSessionLocal() as session:
            # Аватары
            avatars = await session.query(UserAvatar).all()
            for avatar in avatars:
                if avatar.user_id not in self.stats["users"]:
                    self.stats["users"][avatar.user_id] = {
                        "avatars": 0,
                        "transcripts": 0,
                        "history": 0,
                        "total_size": 0
                    }
                
                try:
                    photo_metadata = await storage_utils.get_file_metadata("avatars", avatar.photo_key)
                    preview_metadata = await storage_utils.get_file_metadata("avatars", avatar.preview_key)
                    
                    self.stats["users"][avatar.user_id]["avatars"] += 1
                    self.stats["users"][avatar.user_id]["total_size"] += (
                        photo_metadata["size"] + preview_metadata["size"]
                    )
                    
                    self.stats["types"]["avatars"]["count"] += 1
                    self.stats["types"]["avatars"]["size"] += (
                        photo_metadata["size"] + preview_metadata["size"]
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for avatar {avatar.id}: {e}")
            
            # Транскрипты
            transcripts = await session.query(UserTranscript).all()
            for transcript in transcripts:
                if transcript.user_id not in self.stats["users"]:
                    self.stats["users"][transcript.user_id] = {
                        "avatars": 0,
                        "transcripts": 0,
                        "history": 0,
                        "total_size": 0
                    }
                
                try:
                    audio_metadata = await storage_utils.get_file_metadata("transcripts", transcript.audio_key)
                    transcript_metadata = await storage_utils.get_file_metadata("transcripts", transcript.transcript_key)
                    
                    self.stats["users"][transcript.user_id]["transcripts"] += 1
                    self.stats["users"][transcript.user_id]["total_size"] += (
                        audio_metadata["size"] + transcript_metadata["size"]
                    )
                    
                    self.stats["types"]["transcripts"]["count"] += 1
                    self.stats["types"]["transcripts"]["size"] += (
                        audio_metadata["size"] + transcript_metadata["size"]
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for transcript {transcript.id}: {e}")
            
            # История
            history_entries = await session.query(UserHistory).all()
            for history in history_entries:
                if history.user_id not in self.stats["users"]:
                    self.stats["users"][history.user_id] = {
                        "avatars": 0,
                        "transcripts": 0,
                        "history": 0,
                        "total_size": 0
                    }
                
                try:
                    content_metadata = await storage_utils.get_file_metadata("documents", history.content_key)
                    
                    self.stats["users"][history.user_id]["history"] += 1
                    self.stats["users"][history.user_id]["total_size"] += content_metadata["size"]
                    
                    self.stats["types"]["history"]["count"] += 1
                    self.stats["types"]["history"]["size"] += content_metadata["size"]
                    
                except Exception as e:
                    logger.error(f"Failed to get stats for history {history.id}: {e}")
    
    def print_stats(self):
        """Вывод статистики использования"""
        logger.info("\nMinIO Usage Statistics:")
        
        # Общая статистика
        logger.info(f"\nTotal Storage Used: {self._format_size(self.stats['total_size'])}")
        
        # Статистика по bucket'ам
        logger.info("\nBucket Statistics:")
        for bucket, stats in self.stats["buckets"].items():
            logger.info(f"\n{bucket.capitalize()}:")
            logger.info(f"  Files: {stats['count']}")
            logger.info(f"  Size: {self._format_size(stats['size'])}")
        
        # Статистика по типам данных
        logger.info("\nData Type Statistics:")
        for data_type, stats in self.stats["types"].items():
            logger.info(f"\n{data_type.capitalize()}:")
            logger.info(f"  Files: {stats['count']}")
            logger.info(f"  Size: {self._format_size(stats['size'])}")
        
        # Статистика по пользователям
        logger.info("\nUser Statistics:")
        for user_id, stats in self.stats["users"].items():
            logger.info(f"\nUser {user_id}:")
            logger.info(f"  Avatars: {stats['avatars']}")
            logger.info(f"  Transcripts: {stats['transcripts']}")
            logger.info(f"  History Entries: {stats['history']}")
            logger.info(f"  Total Size: {self._format_size(stats['total_size'])}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Форматирование размера в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

async def main():
    """Основная функция мониторинга"""
    logger.info("Starting MinIO usage monitoring...")
    
    monitor = MinIOUsageMonitor()
    
    try:
        await monitor.collect_stats()
        monitor.print_stats()
        logger.info("Monitoring completed successfully")
        
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 