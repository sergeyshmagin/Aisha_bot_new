"""
Модуль загрузки изображений
Оптимизированная загрузка с множественными попытками и кэшированием
"""
import aiohttp
import asyncio
from typing import Optional

from app.core.logger import get_logger
from ..cache import ultra_gallery_cache

logger = get_logger(__name__)

# Константы загрузки (выносим магические числа)
DEFAULT_TIMEOUT = 5  # Основной таймаут загрузки (сек)
FAST_TIMEOUT = 3     # Быстрый таймаут для альтернативных путей (сек)
ULTRA_FAST_TIMEOUT = 2  # Ультрабыстрый для MinIO refresh (сек)


class ImageLoader:
    """Загрузчик изображений с оптимизациями"""
    
    async def download_image_ultra_fast(self, url: str) -> Optional[bytes]:
        """🚀 УЛЬТРАБЫСТРАЯ загрузка изображения с множественными попытками"""
        
        try:
            # 🎯 СНАЧАЛА проверяем кэш
            cached_data = await ultra_gallery_cache.get_cached_image(url)
            if cached_data:
                logger.debug(f"🚀 ULTRA FAST image load from cache: {len(cached_data)} bytes")
                return cached_data
            
            logger.debug(f"🔄 Loading image from network: {url[:50]}...")
            
            # ПОПЫТКА 1: Загружаем оригинальный URL
            image_data = await self._try_download_url(url)
            if image_data:
                await ultra_gallery_cache.set_cached_image(url, image_data)
                logger.debug(f"✅ Image loaded and cached: {len(image_data)} bytes")
                return image_data
            
            # ПОПЫТКА 2: URL устарел - обновляем через MinIO
            logger.debug(f"⚠️ Original URL failed, trying refresh: {url[:50]}...")
            updated_data = await self._try_refresh_minio_url_ultra_fast(url)
            if updated_data:
                await ultra_gallery_cache.set_cached_image(url, updated_data)
                logger.debug(f"✅ Image refreshed and cached: {len(updated_data)} bytes")
                return updated_data
            
            # ПОПЫТКА 3: Пробуем варианты путей
            logger.debug(f"⚠️ Trying alternative URL paths: {url[:50]}...")
            alternative_data = await self._try_alternative_paths(url)
            if alternative_data:
                await ultra_gallery_cache.set_cached_image(url, alternative_data)
                logger.debug(f"✅ Image loaded from alternative path: {len(alternative_data)} bytes")
                return alternative_data
            
            logger.warning(f"❌ All attempts failed for URL: {url[:50]}...")
            return None
                        
        except Exception as e:
            logger.debug(f"❌ Image load error: {url[:50]}... - {e}")
            return None
    
    async def _try_download_url(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[bytes]:
        """Попытка загрузки URL с таймаутом"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status == 403:
                        logger.debug(f"URL expired (403): {url[:50]}...")
                        return None
                    else:
                        logger.debug(f"HTTP {response.status}: {url[:50]}...")
                        return None
        except asyncio.TimeoutError:
            logger.debug(f"Timeout loading: {url[:50]}...")
            return None
        except Exception as e:
            logger.debug(f"Error loading: {url[:50]}... - {e}")
            return None
    
    async def _try_alternative_paths(self, original_url: str) -> Optional[bytes]:
        """Пробует альтернативные пути для загрузки изображения"""
        try:
            from app.services.storage.minio import MinioStorage
            import urllib.parse
            
            # Парсим URL
            parsed_url = urllib.parse.urlparse(original_url)
            path_parts = parsed_url.path.strip('/').split('/', 1)
            
            if len(path_parts) < 2:
                return None
            
            bucket = path_parts[0]
            object_name = path_parts[1].split('?')[0]
            
            storage = MinioStorage()
            
            # Варианты путей для поиска
            path_variants = [
                object_name,                        # Оригинальный путь
                f"generated/{object_name}",         # С префиксом generated/
                object_name.replace("generated/", "") if "generated/" in object_name else f"images/{object_name}",
            ]
            
            for variant_path in path_variants:
                try:
                    # Проверяем существование файла
                    if hasattr(storage, 'file_exists'):
                        exists = await storage.file_exists(bucket, variant_path)
                        if not exists:
                            continue
                    
                    # Создаем новый URL
                    new_url = await storage.generate_presigned_url(
                        bucket=bucket,
                        object_name=variant_path,
                        expires=3600
                    )
                    
                    if new_url:
                        # Пробуем загрузить
                        image_data = await self._try_download_url(new_url, timeout=FAST_TIMEOUT)
                        if image_data:
                            logger.debug(f"✅ Alternative path worked: {variant_path}")
                            return image_data
                            
                except Exception as variant_error:
                    logger.debug(f"Variant {variant_path} failed: {variant_error}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Alternative paths error: {e}")
            return None
    
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
                async with session.get(new_url, timeout=aiohttp.ClientTimeout(total=ULTRA_FAST_TIMEOUT)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.debug(f"🚀 ULTRA FAST MinIO refresh: {len(image_data)} bytes")
                        return image_data
                    else:
                        return None
                        
        except Exception as e:
            logger.debug(f"❌ MinIO refresh error (ignored): {e}")
            return None 