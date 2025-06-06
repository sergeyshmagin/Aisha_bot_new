#!/usr/bin/env python3
"""
Скрипт для проверки и исправления URL изображений в MinIO

Проблема: Некоторые файлы сохранены с префиксом "generated/" в пути,
но URL в БД указывают на пути без префикса, что приводит к 404 ошибкам.

Использование:
    python scripts/fix_minio_urls.py --check       # Только проверка
    python scripts/fix_minio_urls.py --fix         # Исправление найденных проблем
"""

import asyncio
import sys
import argparse
from pathlib import Path
import logging

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from app.core.config import settings
from app.services.storage.minio import MinioStorage
from app.repositories.generation_repository import ImageGenerationRepository
from sqlalchemy import select, update
from app.models.generation import ImageGeneration

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MinioUrlFixer:
    """Утилита для исправления проблемных URL в MinIO"""
    
    def __init__(self):
        self.storage = MinioStorage()
        self.fixed_count = 0
        self.problem_count = 0
        
    async def check_and_fix_urls(self, fix_mode: bool = False):
        """
        Проверяет и при необходимости исправляет проблемные URLs
        
        Args:
            fix_mode: True - исправлять найденные проблемы, False - только проверять
        """
        logger.info(f"🔍 Запуск {'исправления' if fix_mode else 'проверки'} URL изображений в MinIO...")
        
        async with get_session() as session:
            # Получаем все генерации с result_urls
            query = select(ImageGeneration).where(
                ImageGeneration.result_urls.isnot(None),
                ImageGeneration.result_urls != []
            )
            result = await session.execute(query)
            generations = result.scalars().all()
            
            logger.info(f"📊 Найдено {len(generations)} генераций с изображениями")
            
            problems_found = []
            
            for generation in generations:
                if not generation.result_urls:
                    continue
                    
                for i, url in enumerate(generation.result_urls):
                    if not url or not url.startswith('http'):
                        continue
                        
                    # Анализируем URL
                    problem_type = await self._analyze_url(url)
                    
                    if problem_type:
                        self.problem_count += 1
                        problem_info = {
                            'generation_id': generation.id,
                            'url_index': i,
                            'old_url': url,
                            'problem_type': problem_type
                        }
                        
                        logger.warning(f"⚠️  Проблема #{self.problem_count}: {problem_type}")
                        logger.warning(f"   Генерация: {generation.id}")
                        logger.warning(f"   URL: {url[:80]}...")
                        
                        if fix_mode:
                            # Пытаемся исправить URL
                            fixed_url = await self._fix_url(url, problem_type)
                            if fixed_url and fixed_url != url:
                                # Обновляем URL в базе данных
                                new_result_urls = generation.result_urls.copy()
                                new_result_urls[i] = fixed_url
                                
                                await session.execute(
                                    update(ImageGeneration)
                                    .where(ImageGeneration.id == generation.id)
                                    .values(result_urls=new_result_urls)
                                )
                                
                                self.fixed_count += 1
                                logger.info(f"✅ Исправлено #{self.fixed_count}: {generation.id}")
                                logger.info(f"   Новый URL: {fixed_url[:80]}...")
                            else:
                                logger.error(f"❌ Не удалось исправить URL для {generation.id}")
                        
                        problems_found.append(problem_info)
            
            if fix_mode and self.fixed_count > 0:
                await session.commit()
                logger.info(f"💾 Сохранено {self.fixed_count} исправлений в базе данных")
            
        # Итоговая статистика
        logger.info(f"📈 Результаты {'исправления' if fix_mode else 'проверки'}:")
        logger.info(f"   🔍 Проверено генераций: {len(generations)}")
        logger.info(f"   ⚠️  Найдено проблем: {self.problem_count}")
        
        if fix_mode:
            logger.info(f"   ✅ Исправлено: {self.fixed_count}")
            logger.info(f"   ❌ Не удалось исправить: {self.problem_count - self.fixed_count}")
        
        return problems_found
    
    async def _analyze_url(self, url: str) -> str:
        """
        Анализирует URL на наличие проблем
        
        Returns:
            str: Тип проблемы или None если проблем нет
        """
        try:
            import urllib.parse
            
            # Парсим URL
            parsed_url = urllib.parse.urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                return "invalid_format"
            
            bucket = path_parts[0]
            object_name = path_parts[1]
            
            if bucket != "generated":
                return None  # Проверяем только generated bucket
            
            # Проверяем существование файла по оригинальному пути
            try:
                test_data = await self.storage.download_file(bucket, object_name)
                if test_data and len(test_data) > 0:
                    return None  # Файл найден - проблем нет
            except:
                pass
            
            # Проверяем с префиксом generated/
            if not object_name.startswith("generated/"):
                try:
                    prefixed_object_name = f"generated/{object_name}"
                    test_data = await self.storage.download_file(bucket, prefixed_object_name)
                    if test_data and len(test_data) > 0:
                        return "missing_prefix"  # Файл есть с префиксом
                except:
                    pass
            
            return "file_not_found"  # Файл не найден вообще
            
        except Exception as e:
            logger.error(f"Ошибка анализа URL {url}: {e}")
            return "analysis_error"
    
    async def _fix_url(self, old_url: str, problem_type: str) -> str:
        """
        Исправляет проблемный URL
        
        Args:
            old_url: Оригинальный URL
            problem_type: Тип проблемы
            
        Returns:
            str: Исправленный URL или оригинальный если исправить не удалось
        """
        try:
            if problem_type == "missing_prefix":
                # Генерируем новый presigned URL с правильным путём
                import urllib.parse
                
                parsed_url = urllib.parse.urlparse(old_url)
                path_parts = parsed_url.path.strip('/').split('/', 1)
                
                if len(path_parts) >= 2:
                    bucket = path_parts[0]
                    object_name = path_parts[1]
                    
                    # Добавляем префикс для правильного пути
                    corrected_object_name = f"generated/{object_name}"
                    
                    # Генерируем новый presigned URL
                    new_url = await self.storage.generate_presigned_url(
                        bucket=bucket,
                        object_name=corrected_object_name,
                        expires=86400  # 1 день
                    )
                    
                    return new_url if new_url else old_url
            
            return old_url
            
        except Exception as e:
            logger.error(f"Ошибка исправления URL {old_url}: {e}")
            return old_url


async def main():
    """Главная функция скрипта"""
    parser = argparse.ArgumentParser(description='Проверка и исправление URL изображений в MinIO')
    parser.add_argument('--check', action='store_true', help='Только проверить наличие проблем')
    parser.add_argument('--fix', action='store_true', help='Исправить найденные проблемы')
    
    args = parser.parse_args()
    
    if not args.check and not args.fix:
        parser.print_help()
        return
    
    if args.check and args.fix:
        logger.error("❌ Выберите один режим: --check или --fix")
        return
    
    fixer = MinioUrlFixer()
    
    try:
        problems = await fixer.check_and_fix_urls(fix_mode=args.fix)
        
        if args.check and problems:
            logger.info(f"💡 Для исправления {len(problems)} проблем запустите: python scripts/fix_minio_urls.py --fix")
        
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 