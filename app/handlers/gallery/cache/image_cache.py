"""
Модуль управления кэшем изображений
Предзагрузка и оптимизация доступа к изображениям
"""
import aiohttp
import asyncio
import random
from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.database.models import ImageGeneration
from .ultra_fast_cache import ultra_gallery_cache

logger = get_logger(__name__)

# Константы кэширования (выносим магические числа)
PREFETCH_RANGE = 5  # Количество изображений для предзагрузки в каждую сторону
RANDOM_PREFETCH_COUNT = 10  # Количество случайных изображений для предзагрузки
PRIORITY_TIMEOUT = 3  # Таймаут для приоритетных изображений (сек)
BACKGROUND_TIMEOUT = 8  # Таймаут для фоновых изображений (сек)
PREFETCH_WAIT_TIMEOUT = 2  # Время ожидания приоритетной предзагрузки (сек)


class ImageCacheManager:
    """Управление кэшем изображений с агрессивной предзагрузкой"""
    
    def __init__(self):
        self._prefetch_tasks = {}  # Задачи предзагрузки
    
    async def prefetch_adjacent_images(self, images: List[ImageGeneration], current_idx: int):
        """🚀 МАКСИМАЛЬНО АГРЕССИВНАЯ предзагрузка для мгновенной навигации"""
        
        prefetch_indices = []
        
        # Предзагружаем изображения в обе стороны
        for offset in range(-PREFETCH_RANGE, PREFETCH_RANGE + 1):
            if offset == 0:  # Пропускаем текущее изображение
                continue
            idx = current_idx + offset
            if 0 <= idx < len(images):
                prefetch_indices.append(idx)
        
        # Также предзагружаем несколько случайных изображений для лучшего покрытия
        random_indices = random.sample(range(len(images)), min(RANDOM_PREFETCH_COUNT, len(images)))
        for idx in random_indices:
            if idx not in prefetch_indices and idx != current_idx:
                prefetch_indices.append(idx)
        
        logger.debug(f"🚀 МАКСИМАЛЬНАЯ предзагрузка: {len(prefetch_indices)} изображений (current: {current_idx})")
        
        # Запускаем предзагрузку параллельно с приоритетом
        priority_tasks = []  # Соседние изображения (высокий приоритет)
        background_tasks = []  # Случайные изображения (низкий приоритет)
        
        for idx in prefetch_indices:
            generation = images[idx]
            if generation.result_urls and len(generation.result_urls) > 0:
                url = generation.result_urls[0]
                
                # Проверяем что изображение еще не кэшировано
                cached_image = await ultra_gallery_cache.get_cached_image(url)
                if not cached_image:
                    task_key = f"prefetch_{url}"
                    
                    # Избегаем дублированных задач предзагрузки
                    if task_key not in self._prefetch_tasks:
                        # Определяем приоритет (соседние vs случайные)
                        is_adjacent = abs(idx - current_idx) <= PREFETCH_RANGE
                        
                        if is_adjacent:
                            task = asyncio.create_task(
                                self._prefetch_single_image_priority(url, high_priority=True)
                            )
                            priority_tasks.append(task)
                        else:
                            task = asyncio.create_task(
                                self._prefetch_single_image_priority(url, high_priority=False)
                            )
                            background_tasks.append(task)
                        
                        self._prefetch_tasks[task_key] = task
        
        # Ждем завершения приоритетных задач (не блокируя UI)
        if priority_tasks:
            asyncio.create_task(self._wait_priority_prefetch(priority_tasks))
    
    async def _wait_priority_prefetch(self, priority_tasks):
        """Ждет завершения приоритетных задач предзагрузки"""
        try:
            # Ждем максимум 2 секунды для приоритетных изображений
            await asyncio.wait_for(
                asyncio.gather(*priority_tasks, return_exceptions=True),
                timeout=PREFETCH_WAIT_TIMEOUT
            )
            logger.debug("✅ Приоритетная предзагрузка завершена")
        except asyncio.TimeoutError:
            logger.debug("⏱️ Таймаут приоритетной предзагрузки (это нормально)")
        except Exception as e:
            logger.debug(f"❌ Ошибка приоритетной предзагрузки: {e}")
    
    async def _prefetch_single_image_priority(self, url: str, high_priority: bool = True):
        """🔄 Предзагружает одно изображение с приоритизацией"""
        try:
            # Проверяем что изображение еще не кэшировано
            cached = await ultra_gallery_cache.get_cached_image(url)
            if cached:
                return
            
            # Настраиваем таймаут в зависимости от приоритета
            timeout = PRIORITY_TIMEOUT if high_priority else BACKGROUND_TIMEOUT
            
            # Загружаем изображение
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        data = await response.read()
                        await ultra_gallery_cache.set_cached_image(url, data)
                        priority_text = "HIGH" if high_priority else "LOW"
                        logger.debug(f"🚀 PREFETCH {priority_text}: {url[:50]}... ({len(data)} байт)")
                    elif response.status == 403:
                        # URL устарел - пытаемся обновить только для высокого приоритета
                        if high_priority:
                            updated_data = await self._try_refresh_minio_url_ultra_fast(url)
                            if updated_data:
                                await ultra_gallery_cache.set_cached_image(url, updated_data)
                                logger.debug(f"🚀 PREFETCH HIGH REFRESHED: {url[:50]}... ({len(updated_data)} байт)")
                    else:
                        logger.debug(f"🚀 PREFETCH FAILED: {url[:50]}... (HTTP {response.status})")
            
        except asyncio.TimeoutError:
            priority_text = "HIGH" if high_priority else "LOW"
            logger.debug(f"⏱️ PREFETCH {priority_text} TIMEOUT: {url[:50]}...")
        except Exception as e:
            logger.debug(f"🚀 PREFETCH ERROR: {url[:50]}... - {e}")
        finally:
            # Удаляем задачу из списка активных
            task_key = f"prefetch_{url}"
            if task_key in self._prefetch_tasks:
                del self._prefetch_tasks[task_key]
    
    async def _try_refresh_minio_url_ultra_fast(self, old_url: str) -> Optional[bytes]:
        """🚀 УЛЬТРАБЫСТРОЕ обновление устаревшего MinIO URL"""
        
        try:
            from app.services.storage.minio import MinioStorage
            import urllib.parse
            
            # Парсим URL
            parsed_url = urllib.parse.urlparse(old_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                return None
            
            bucket = path_parts[0]
            object_name = path_parts[1].split('?')[0]
            
            # 🚀 ИСПОЛЬЗУЕМ ТОЛЬКО работающий путь (из логов - "вариант 2")
            correct_path = f"generated/{object_name}"
            
            storage = MinioStorage()
            
            # Создаем новый URL с коротким временем жизни для скорости
            new_url = await storage.generate_presigned_url(
                bucket=bucket,
                object_name=correct_path,
                expires=3600  # 1 час (вместо суток)
            )
            
            if not new_url:
                return None
            
            # Загружаем по новому URL с коротким таймаутом
            async with aiohttp.ClientSession() as session:
                async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.debug(f"🚀 ULTRA FAST MinIO refresh: {len(image_data)} bytes")
                        return image_data
                    else:
                        return None
                        
        except Exception as e:
            logger.debug(f"❌ MinIO refresh error (ignored): {e}")
            return None 