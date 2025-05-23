#!/usr/bin/env python3
"""
Тестовый скрипт для проверки репозитория транскриптов
"""
import asyncio
import logging
from uuid import UUID
from aisha_v2.app.database.session import get_session
from aisha_v2.app.database.repositories.transcript import TranscriptRepository

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_transcript_repo():
    """Тестирует работу репозитория транскриптов"""
    logger.info("Запуск теста репозитория транскриптов")
    
    # Тестовый user_id из логов
    user_id = UUID('1d19093b-4eba-4352-85b0-2f64713ff39c')
    logger.info(f"Тестируем с user_id: {user_id}")
    
    try:
        async with get_session() as session:
            repo = TranscriptRepository(session)
            logger.info("Репозиторий создан")
            
            # Тестируем получение транскриптов
            logger.info("Вызываем get_user_transcripts...")
            transcripts = await repo.get_user_transcripts(user_id, limit=5, offset=0)
            logger.info(f"Получено {len(transcripts)} транскриптов")
            
            # Проверяем каждый транскрипт
            for i, transcript in enumerate(transcripts):
                logger.info(f"Транскрипт {i}: id={transcript.id}, type={type(transcript)}")
                logger.info(f"  user_id: {transcript.user_id} ({type(transcript.user_id)})")
                logger.info(f"  created_at: {transcript.created_at} ({type(transcript.created_at)})")
                logger.info(f"  metadata: {transcript.transcript_metadata}")
                
                # Тестируем конвертацию в словарь
                try:
                    transcript_dict = {
                        "id": str(transcript.id),
                        "created_at": transcript.created_at.isoformat() if transcript.created_at else None,
                        "metadata": transcript.transcript_metadata
                    }
                    logger.info(f"  Конвертация в dict успешна: {transcript_dict}")
                except Exception as e:
                    logger.error(f"  Ошибка конвертации в dict: {e}")
                    raise
                    
    except Exception as e:
        logger.exception(f"Ошибка в тесте: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_transcript_repo()) 