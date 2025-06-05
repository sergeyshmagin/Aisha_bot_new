"""
Модуль управления файлами для FAL AI
"""
import asyncio
import io
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import aiohttp
from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger
from app.services.storage.minio import MinioStorage

logger = get_logger(__name__)


class FalFileManager:
    """Управление файлами и архивами для FAL AI"""
    
    def __init__(self):
        self.temp_files = []
        self.minio_storage = MinioStorage()
    
    async def download_and_create_archive(
        self, 
        photo_urls: List[str], 
        avatar_id: UUID
    ) -> Optional[str]:
        """
        Скачивает фотографии и создает архив для обучения
        
        Args:
            photo_urls: Список ключей MinIO фотографий
            avatar_id: ID аватара
            
        Returns:
            Optional[str]: URL загруженного архива или None при ошибке
        """
        try:
            logger.info(f"[FAL Files] Скачивание {len(photo_urls)} фотографий для аватара {avatar_id}")
            
            # 1. Скачиваем фотографии
            photo_paths = await self.download_photos_from_minio(photo_urls, avatar_id)
            
            if not photo_paths:
                logger.error(f"[FAL Files] Не удалось скачать фотографии для аватара {avatar_id}")
                return None
            
            # 2. Создаем и загружаем архив
            data_url = await self.create_and_upload_archive(photo_paths, avatar_id)
            
            if data_url:
                logger.info(f"[FAL Files] Архив создан успешно: {data_url}")
            else:
                logger.error(f"[FAL Files] Не удалось создать архив для аватара {avatar_id}")
            
            return data_url
            
        except Exception as e:
            logger.exception(f"[FAL Files] Ошибка создания архива для аватара {avatar_id}: {e}")
            return None
    
    async def download_photos_from_minio(
        self, 
        photo_keys: List[str], 
        avatar_id: UUID
    ) -> List[Path]:
        """
        Скачивает фотографии из MinIO
        
        Args:
            photo_keys: Список ключей MinIO фотографий
            avatar_id: ID аватара
            
        Returns:
            List[Path]: Список путей к скачанным файлам
        """
        photo_paths = []
        
        try:
            # Создаем временную директорию
            temp_dir = Path(tempfile.mkdtemp(prefix=f"avatar_{avatar_id}_"))
            self.temp_files.append(temp_dir)
            
            logger.info(f"[FAL Files] Скачивание в {temp_dir}")
            
            # ИСПРАВЛЕНИЕ: Используем правильный bucket для аватаров
            bucket = settings.MINIO_BUCKET_AVATARS  # 'avatars' вместо 'aisha'
            logger.info(f"[FAL Files] Используем bucket: {bucket}")
            
            async with aiohttp.ClientSession() as session:
                for i, minio_key in enumerate(photo_keys):
                    try:
                        logger.debug(f"[FAL Files] Скачивание фото {i+1}/{len(photo_keys)}: {minio_key}")
                        
                        # Генерируем presigned URL для скачивания
                        download_url = await self.minio_storage.generate_presigned_url(
                            bucket=bucket,
                            object_name=minio_key,
                            expires=3600  # 1 час
                        )
                        
                        if not download_url:
                            logger.error(f"[FAL Files] Не удалось создать presigned URL для {minio_key}")
                            continue
                        
                        logger.debug(f"[FAL Files] Presigned URL создан для {minio_key}")
                        
                        async with session.get(download_url) as response:
                            if response.status == 200:
                                # Получаем содержимое файла
                                content = await response.read()
                                
                                # Проверяем что это изображение
                                try:
                                    img = Image.open(io.BytesIO(content))
                                    img.verify()  # Проверяем целостность
                                    
                                    # Определяем расширение
                                    format_ext = img.format.lower() if img.format else 'jpg'
                                    if format_ext == 'jpeg':
                                        format_ext = 'jpg'
                                    
                                    # Сохраняем файл
                                    file_path = temp_dir / f"photo_{i+1:03d}.{format_ext}"
                                    
                                    # Переоткрываем изображение для сохранения
                                    img = Image.open(io.BytesIO(content))
                                    img.save(file_path)
                                    
                                    photo_paths.append(file_path)
                                    logger.debug(f"[FAL Files] Сохранено: {file_path}")
                                    
                                except Exception as img_error:
                                    logger.error(f"[FAL Files] Ошибка обработки изображения {minio_key}: {img_error}")
                                    continue
                            else:
                                logger.error(f"[FAL Files] Ошибка скачивания {minio_key}: HTTP {response.status}")
                                continue
                                
                    except Exception as e:
                        logger.error(f"[FAL Files] Ошибка скачивания фото {minio_key}: {e}")
                        continue
            
            logger.info(f"[FAL Files] Скачано {len(photo_paths)} из {len(photo_keys)} фотографий")
            return photo_paths
            
        except Exception as e:
            logger.exception(f"[FAL Files] Критическая ошибка скачивания фотографий: {e}")
            return []
    
    async def create_and_upload_archive(
        self, 
        photo_paths: List[Path], 
        avatar_id: UUID
    ) -> Optional[str]:
        """
        Создает ZIP архив и загружает его в FAL AI
        
        Args:
            photo_paths: Список путей к фотографиям
            avatar_id: ID аватара
            
        Returns:
            Optional[str]: URL загруженного архива
        """
        try:
            if not photo_paths:
                logger.error(f"[FAL Files] Нет фотографий для создания архива аватара {avatar_id}")
                return None
            
            # Создаем временный ZIP файл
            temp_zip = Path(tempfile.mktemp(suffix=f"_avatar_{avatar_id}.zip"))
            self.temp_files.append(temp_zip)
            
            logger.info(f"[FAL Files] Создание архива {temp_zip} с {len(photo_paths)} фотографиями")
            
            # Создаем ZIP архив
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for photo_path in photo_paths:
                    if photo_path.exists():
                        # Добавляем файл в архив с простым именем
                        arcname = photo_path.name
                        zipf.write(photo_path, arcname)
                        logger.debug(f"[FAL Files] Добавлен в архив: {arcname}")
                    else:
                        logger.warning(f"[FAL Files] Файл не найден: {photo_path}")
            
            # Проверяем размер архива
            archive_size = temp_zip.stat().st_size
            logger.info(f"[FAL Files] Архив создан: {archive_size} байт")
            
            # Загружаем архив в FAL AI
            data_url = await self._upload_archive_to_fal(temp_zip)
            
            return data_url
            
        except Exception as e:
            logger.exception(f"[FAL Files] Ошибка создания архива для аватара {avatar_id}: {e}")
            return None
    
    async def _upload_archive_to_fal(self, archive_path: Path) -> Optional[str]:
        """
        Загружает архив в FAL AI storage
        
        Args:
            archive_path: Путь к архиву
            
        Returns:
            Optional[str]: URL загруженного файла
        """
        try:
            import fal_client
            import os
            
            logger.info(f"[FAL Files] Загрузка архива {archive_path} в FAL AI")
            
            # ИСПРАВЛЕНИЕ: Устанавливаем FAL API ключ из настроек
            fal_api_key = settings.effective_fal_api_key
            if not fal_api_key:
                raise ValueError("FAL API ключ не настроен в конфигурации")
            
            # Временно устанавливаем переменную среды для fal_client
            original_fal_key = os.environ.get('FAL_KEY')
            os.environ['FAL_KEY'] = fal_api_key
            
            try:
                # Передаем путь к файлу как строку
                file_url = fal_client.upload_file(str(archive_path))
                
                logger.info(f"[FAL Files] Архив загружен успешно: {file_url}")
                return file_url
            finally:
                # Восстанавливаем оригинальное значение переменной среды
                if original_fal_key is not None:
                    os.environ['FAL_KEY'] = original_fal_key
                else:
                    os.environ.pop('FAL_KEY', None)
            
        except Exception as e:
            logger.exception(f"[FAL Files] Ошибка загрузки архива {archive_path}: {e}")
            return None
    
    async def cleanup_temp_files(self):
        """Очищает временные файлы"""
        try:
            for temp_path in self.temp_files:
                try:
                    if temp_path.exists():
                        if temp_path.is_dir():
                            # Удаляем директорию рекурсивно
                            import shutil
                            shutil.rmtree(temp_path)
                            logger.debug(f"[FAL Files] Удалена временная директория: {temp_path}")
                        else:
                            # Удаляем файл
                            temp_path.unlink()
                            logger.debug(f"[FAL Files] Удален временный файл: {temp_path}")
                except Exception as e:
                    logger.warning(f"[FAL Files] Не удалось удалить {temp_path}: {e}")
            
            self.temp_files.clear()
            logger.debug("[FAL Files] Очистка временных файлов завершена")
            
        except Exception as e:
            logger.exception(f"[FAL Files] Ошибка очистки временных файлов: {e}") 