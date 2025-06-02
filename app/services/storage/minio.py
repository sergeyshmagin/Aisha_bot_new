import io
from minio import Minio, S3Error
from app.core.config import settings
import asyncio
from datetime import timedelta

class MinioStorage:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

    async def upload_file(self, bucket: str, object_name: str, data: bytes, content_type: str = None) -> str:
        """
        Загружает файл в MinIO
        
        Args:
            bucket: Имя бакета
            object_name: Имя объекта (путь к файлу)
            data: Данные файла
            content_type: MIME тип файла
            
        Returns:
            str: Путь к загруженному файлу (object_name)
            
        Raises:
            Exception: При ошибке загрузки
        """
        loop = asyncio.get_event_loop()
        try:
            if not await loop.run_in_executor(None, lambda: self.client.bucket_exists(bucket)):
                await loop.run_in_executor(None, lambda: self.client.make_bucket(bucket))
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    bucket,
                    object_name,
                    io.BytesIO(data),
                    len(data),
                    content_type=content_type
                )
            )
            return object_name  # Возвращаем путь к файлу вместо True
        except S3Error as e:
            # Логируем ошибку и пробрасываем исключение
            raise Exception(f"Ошибка загрузки файла в MinIO: {str(e)}")

    async def download_file(self, bucket: str, object_name: str) -> bytes:
        loop = asyncio.get_event_loop()
        try:
            print(f"DEBUG: MinioStorage.download_file: bucket={bucket}, object_name={object_name}")
            response = await loop.run_in_executor(
                None, lambda: self.client.get_object(bucket, object_name)
            )
            data = response.read()
            print(f"DEBUG: MinioStorage.download_file: получено {len(data)} байт")
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            print(f"DEBUG: MinioStorage.download_file: ОШИБКА {str(e)}")
            return b""

    async def delete_file(self, bucket: str, object_name: str) -> bool:
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: self.client.remove_object(bucket, object_name))
            return True
        except S3Error:
            return False

    async def generate_presigned_url(self, bucket: str, object_name: str, expires: int = 3600) -> str:
        loop = asyncio.get_event_loop()
        try:
            # Проверяем валидный диапазон для MinIO (от 1 секунды до 7 дней)
            max_expires = 7 * 24 * 3600  # 7 дней в секундах
            min_expires = 1
            
            if expires > max_expires:
                expires = max_expires
                print(f"DEBUG: MinioStorage.generate_presigned_url: expires сокращен до максимального значения {max_expires}")
            elif expires < min_expires:
                expires = min_expires
                print(f"DEBUG: MinioStorage.generate_presigned_url: expires увеличен до минимального значения {min_expires}")
            
            print(f"DEBUG: MinioStorage.generate_presigned_url: bucket={bucket}, object={object_name}, expires={expires}s")
            
            url = await loop.run_in_executor(
                None,
                lambda: self.client.presigned_get_object(
                    bucket, 
                    object_name, 
                    expires=timedelta(seconds=expires)
                )
            )
            print(f"DEBUG: MinioStorage.generate_presigned_url: URL создан успешно")
            return url
        except Exception as e:
            print(f"DEBUG: MinioStorage.generate_presigned_url: ОШИБКА {str(e)}")
            return ""
