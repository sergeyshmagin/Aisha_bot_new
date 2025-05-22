"""
Клиент для работы с MinIO.
"""

import logging
from typing import Optional, Union
from minio import Minio
from minio.error import S3Error
from frontend_bot.config import settings
import io
import asyncio
from datetime import timedelta

logger = logging.getLogger(__name__)

# Инициализация клиента MinIO
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

def ensure_bucket_exists(bucket_name: str):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

async def upload_file(
    bucket: str,
    object_name: str,
    data: Union[bytes, str, io.BytesIO],
    content_type: Optional[str] = None
) -> bool:
    """
    Загружает файл в MinIO.
    
    Args:
        bucket (str): Имя бакета
        object_name (str): Имя объекта
        data (Union[bytes, str, io.BytesIO]): Данные для загрузки
        content_type (Optional[str]): Тип контента
        
    Returns:
        bool: True если загрузка успешна, False иначе
    """
    try:
        # Проверяем существование бакета
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
        
        # Преобразуем данные и определяем длину
        if isinstance(data, str):
            data = data.encode()
            length = len(data)
        elif isinstance(data, bytes):
            length = len(data)
            data = io.BytesIO(data)
        elif isinstance(data, io.BytesIO):
            data.seek(0)
            length = data.getbuffer().nbytes
        else:
            raise TypeError(f"upload_file: неподдерживаемый тип данных: {type(data)}")
        
        minio_client.put_object(
            bucket,
            object_name,
            data,
            length,
            content_type=content_type
        )
        
        return True
        
    except S3Error as e:
        logger.error(f"Ошибка при загрузке файла в MinIO: {e}")
        return False

async def generate_presigned_url(bucket: str, object_name: str, expires: int = 3600) -> str:
    """
    Генерирует presigned URL для доступа к файлу.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: minio_client.presigned_get_object(
            bucket, object_name, expires=timedelta(seconds=expires)
        )
    )

async def download_file(bucket: str, object_name: str) -> bytes:
    """
    Скачивает файл из MinIO.
    """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: minio_client.get_object(bucket, object_name))
    data = response.read()
    response.close()
    response.release_conn()
    return data

async def check_file_exists(bucket: str, object_name: str) -> bool:
    """
    Проверяет существование файла в MinIO.
    """
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: minio_client.stat_object(bucket, object_name))
        return True
    except S3Error:
        return False

async def delete_file(
    bucket: str,
    object_name: str
) -> bool:
    """
    Удаляет файл из MinIO.
    
    Args:
        bucket (str): Имя бакета
        object_name (str): Имя объекта
        
    Returns:
        bool: True если удаление успешно, False иначе
    """
    try:
        minio_client.remove_object(bucket, object_name)
        return True
        
    except S3Error as e:
        logger.error(f"Ошибка при удалении файла из MinIO: {e}")
        return False 