"""
Утилиты для работы с MinIO.
"""

import os
import io
import json
from typing import Optional, Dict, Any, BinaryIO, Union, List
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
from frontend_bot.config.external_services import (
    EXTERNAL_SERVICES,
    MINIO_BUCKETS,
    RETENTION_POLICIES,
    BUCKET_STRUCTURES
)
from frontend_bot.utils.logger import get_logger

logger = get_logger(__name__)

# Инициализация клиента MinIO
minio_client = Minio(
    EXTERNAL_SERVICES["minio"]["endpoint"],
    access_key=EXTERNAL_SERVICES["minio"]["access_key"],
    secret_key=EXTERNAL_SERVICES["minio"]["secret_key"],
    secure=EXTERNAL_SERVICES["minio"]["secure"]
)

async def init_storage() -> None:
    """Инициализирует хранилище MinIO."""
    try:
        # Создаем бакеты если их нет
        for bucket_name in MINIO_BUCKETS.values():
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                logger.info(f"Создан бакет: {bucket_name}")
                
                # Устанавливаем политику хранения
                if bucket_name in RETENTION_POLICIES and RETENTION_POLICIES[bucket_name]:
                    days = RETENTION_POLICIES[bucket_name]
                    policy = {
                        "Rules": [
                            {
                                "ID": f"expire-{bucket_name}",
                                "Status": "Enabled",
                                "Expiration": {
                                    "Days": days
                                }
                            }
                        ]
                    }
                    minio_client.set_bucket_lifecycle(bucket_name, json.dumps(policy))
                    logger.info(f"Установлена политика хранения для {bucket_name}: {days} дней")
    except S3Error as e:
        logger.error(f"Ошибка при инициализации хранилища: {e}")
        raise

def get_object_path(bucket_type: str, **kwargs) -> str:
    """
    Генерирует путь к объекту в бакете.
    
    Args:
        bucket_type: Тип бакета (avatars, transcripts, documents, temp)
        **kwargs: Параметры для подстановки в шаблон пути
    
    Returns:
        str: Путь к объекту
    """
    if bucket_type not in BUCKET_STRUCTURES:
        raise ValueError(f"Неизвестный тип бакета: {bucket_type}")
    
    structure = BUCKET_STRUCTURES[bucket_type]
    pattern = structure["pattern"]
    
    # Добавляем timestamp для временных файлов
    if bucket_type == "temp" and "timestamp" not in kwargs:
        kwargs["timestamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return pattern.format(**kwargs)

async def upload_file(
    bucket: str,
    object_name: str,
    data: Union[bytes, BinaryIO],
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Загружает файл в MinIO.
    
    Args:
        bucket: Имя бакета
        object_name: Имя объекта
        data: Данные файла или объект с методом read()
        content_type: MIME-тип
        metadata: Метаданные
    """
    try:
        # Если data это bytes, оборачиваем в BytesIO
        if isinstance(data, bytes):
            data = io.BytesIO(data)
            length = len(data.getvalue())
        else:
            # Если это файловый объект, определяем размер
            data.seek(0, os.SEEK_END)
            length = data.tell()
            data.seek(0)
        
        minio_client.put_object(
            bucket,
            object_name,
            data,
            length,
            content_type=content_type,
            metadata=metadata
        )
        logger.info(f"Файл загружен: {bucket}/{object_name}")
    except S3Error as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        raise

async def download_file(bucket: str, object_name: str) -> bytes:
    """
    Скачивает файл из MinIO.
    
    Args:
        bucket: Имя бакета
        object_name: Имя объекта
    
    Returns:
        bytes: Данные файла
    """
    try:
        response = minio_client.get_object(bucket, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        logger.error(f"Ошибка при скачивании файла: {e}")
        raise

async def delete_file(bucket: str, object_name: str) -> None:
    """
    Удаляет файл из MinIO.
    
    Args:
        bucket: Имя бакета
        object_name: Имя объекта
    """
    try:
        minio_client.remove_object(bucket, object_name)
        logger.info(f"Файл удален: {bucket}/{object_name}")
    except S3Error as e:
        logger.error(f"Ошибка при удалении файла: {e}")
        raise

async def generate_presigned_url(
    bucket: str,
    object_name: str,
    expires: int = 3600
) -> str:
    """
    Генерирует presigned URL для доступа к файлу.
    
    Args:
        bucket: Имя бакета
        object_name: Имя объекта
        expires: Время жизни URL в секундах
    
    Returns:
        str: Presigned URL
    """
    try:
        return minio_client.presigned_get_object(bucket, object_name, expires=expires)
    except S3Error as e:
        logger.error(f"Ошибка при генерации presigned URL: {e}")
        raise

async def get_file_metadata(bucket: str, object_name: str) -> Dict[str, Any]:
    """
    Получает метаданные файла.
    
    Args:
        bucket: Имя бакета
        object_name: Имя объекта
    
    Returns:
        Dict[str, Any]: Метаданные файла
    """
    try:
        stat = minio_client.stat_object(bucket, object_name)
        return {
            "size": stat.size,
            "last_modified": stat.last_modified,
            "content_type": stat.content_type,
            "metadata": stat.metadata
        }
    except S3Error as e:
        logger.error(f"Ошибка при получении метаданных файла: {e}")
        raise

async def list_objects(
    bucket: str,
    prefix: Optional[str] = None,
    recursive: bool = True
) -> List[Dict[str, Any]]:
    """
    Получает список объектов в бакете.
    
    Args:
        bucket: Имя бакета
        prefix: Префикс для фильтрации
        recursive: Рекурсивный поиск
    
    Returns:
        List[Dict[str, Any]]: Список объектов
    """
    try:
        objects = minio_client.list_objects(bucket, prefix=prefix, recursive=recursive)
        return [
            {
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified,
                "is_dir": obj.is_dir
            }
            for obj in objects
        ]
    except S3Error as e:
        logger.error(f"Ошибка при получении списка объектов: {e}")
        raise

async def copy_object(
    source_bucket: str,
    source_object: str,
    dest_bucket: str,
    dest_object: str
) -> None:
    """
    Копирует объект между бакетами.
    
    Args:
        source_bucket: Исходный бакет
        source_object: Исходный объект
        dest_bucket: Целевой бакет
        dest_object: Целевой объект
    """
    try:
        minio_client.copy_object(
            dest_bucket,
            dest_object,
            f"{source_bucket}/{source_object}"
        )
        logger.info(f"Объект скопирован: {source_bucket}/{source_object} -> {dest_bucket}/{dest_object}")
    except S3Error as e:
        logger.error(f"Ошибка при копировании объекта: {e}")
        raise 