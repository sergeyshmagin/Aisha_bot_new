"""
Интеграционные тесты для storage_utils.py.
"""

import os
import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from shared_storage import storage_utils
from frontend_bot.config.external_services import MINIO_BUCKETS, BUCKET_STRUCTURES

MINIO_BUCKET = os.getenv("MINIO_BUCKET", "test-bucket")

@pytest.fixture(scope="function")
async def test_bucket():
    """Фикстура для создания тестового bucket'а"""
    bucket_name = f"test-{uuid.uuid4().hex[:8]}"
    client = storage_utils.minio_client
    loop = asyncio.get_event_loop()
    found = await loop.run_in_executor(None, client.bucket_exists, bucket_name)
    if not found:
        await loop.run_in_executor(None, client.make_bucket, bucket_name)
    yield bucket_name
    # Очистка после тестов не требуется, так как bucket временный

@pytest.mark.asyncio
async def test_init_storage():
    """Тест инициализации хранилища"""
    await storage_utils.init_storage()
    for bucket_name in MINIO_BUCKETS.values():
        assert storage_utils.minio_client.bucket_exists(bucket_name)

@pytest.mark.asyncio
async def test_get_object_path():
    """Тест генерации путей к объектам"""
    # Тест для аватаров
    avatar_path = storage_utils.get_object_path(
        "avatars",
        user_id=123,
        avatar_id="abc",
        file_type="original.png"
    )
    assert avatar_path == "users/123/avatars/abc/original.png"
    
    # Тест для транскриптов
    transcript_path = storage_utils.get_object_path(
        "transcripts",
        user_id=123,
        session_id="xyz",
        file_type="transcript.txt"
    )
    assert transcript_path == "users/123/transcripts/xyz/transcript.txt"
    
    # Тест для временных файлов
    temp_path = storage_utils.get_object_path(
        "temp",
        user_id=123,
        file_name="test.txt"
    )
    assert temp_path.startswith("temp/123/")
    assert temp_path.endswith("/test.txt")

@pytest.mark.asyncio
async def test_upload_and_download_file(test_bucket):
    """Тест загрузки и скачивания файла"""
    # Подготовка тестовых данных
    test_data = b"test file content"
    object_name = "test.txt"
    
    # Загрузка файла
    await storage_utils.upload_file(
        test_bucket,
        object_name,
        test_data,
        content_type="text/plain",
        metadata={"test": "metadata"}
    )
    
    # Проверка метаданных
    metadata = await storage_utils.get_file_metadata(test_bucket, object_name)
    assert metadata["size"] == len(test_data)
    assert metadata["content_type"] == "text/plain"
    assert metadata["metadata"]["test"] == "metadata"
    
    # Скачивание файла
    downloaded_data = await storage_utils.download_file(test_bucket, object_name)
    assert downloaded_data == test_data

@pytest.mark.asyncio
async def test_presigned_url(test_bucket):
    """Тест генерации presigned URL"""
    # Загрузка тестового файла
    test_data = b"test content"
    object_name = "test.txt"
    await storage_utils.upload_file(test_bucket, object_name, test_data)
    
    # Генерация URL
    url = await storage_utils.generate_presigned_url(test_bucket, object_name, expires=3600)
    assert url.startswith("http")
    assert test_bucket in url
    assert object_name in url

@pytest.mark.asyncio
async def test_list_objects(test_bucket):
    """Тест получения списка объектов"""
    # Загрузка нескольких файлов
    files = {
        "test1.txt": b"content1",
        "test2.txt": b"content2",
        "subdir/test3.txt": b"content3"
    }
    
    for name, content in files.items():
        await storage_utils.upload_file(test_bucket, name, content)
    
    # Получение списка всех объектов
    all_objects = await storage_utils.list_objects(test_bucket)
    assert len(all_objects) == 3
    
    # Получение списка объектов в поддиректории
    subdir_objects = await storage_utils.list_objects(test_bucket, prefix="subdir/")
    assert len(subdir_objects) == 1
    assert subdir_objects[0]["name"] == "subdir/test3.txt"

@pytest.mark.asyncio
async def test_copy_object(test_bucket):
    """Тест копирования объекта"""
    # Создаем второй тестовый бакет
    dest_bucket = f"test-dest-{uuid.uuid4().hex[:8]}"
    client = storage_utils.minio_client
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, client.make_bucket, dest_bucket)
    
    try:
        # Загружаем тестовый файл
        test_data = b"test content"
        source_object = "test.txt"
        await storage_utils.upload_file(test_bucket, source_object, test_data)
        
        # Копируем файл
        dest_object = "copied.txt"
        await storage_utils.copy_object(
            test_bucket,
            source_object,
            dest_bucket,
            dest_object
        )
        
        # Проверяем, что файл скопирован
        copied_data = await storage_utils.download_file(dest_bucket, dest_object)
        assert copied_data == test_data
    finally:
        # Очистка
        await loop.run_in_executor(None, client.remove_bucket, dest_bucket)

@pytest.mark.asyncio
async def test_delete_file(test_bucket):
    """Тест удаления файла"""
    # Загрузка тестового файла
    test_data = b"test content"
    object_name = "test.txt"
    await storage_utils.upload_file(test_bucket, object_name, test_data)
    
    # Проверяем, что файл существует
    objects = await storage_utils.list_objects(test_bucket)
    assert len(objects) == 1
    
    # Удаляем файл
    await storage_utils.delete_file(test_bucket, object_name)
    
    # Проверяем, что файл удален
    objects = await storage_utils.list_objects(test_bucket)
    assert len(objects) == 0

@pytest.mark.asyncio
async def test_storage_utils_upload_download_delete(test_bucket):
    """Тест базовых операций с файлами"""
    data = b"test data for storage utils"
    key = "test_storage_utils/test_file.txt"

    # Upload
    await storage_utils.upload_file(test_bucket, key, data)

    # Download
    downloaded = await storage_utils.download_file(test_bucket, key)
    assert downloaded == data, "download_file должен возвращать исходные данные"

    # Generate presigned URL
    presigned_url = await storage_utils.generate_presigned_url(test_bucket, key)
    assert presigned_url.startswith("http"), "generate_presigned_url должен возвращать URL"

    # Delete
    await storage_utils.delete_file(test_bucket, key)
    # Проверяем, что файл удалён
    with pytest.raises(Exception):
        await storage_utils.download_file(test_bucket, key)

@pytest.mark.asyncio
async def test_storage_utils_list_files(test_bucket):
    """Тест получения списка файлов"""
    # Загружаем несколько файлов
    files = {
        "test1.txt": b"test data 1",
        "test2.txt": b"test data 2",
        "subdir/test3.txt": b"test data 3"
    }
    
    for key, data in files.items():
        await storage_utils.upload_file(test_bucket, key, data)
    
    # Получаем список всех файлов
    client = storage_utils.minio_client
    loop = asyncio.get_event_loop()
    objects = await loop.run_in_executor(None, lambda: list(client.list_objects(test_bucket, recursive=True)))
    all_files = [obj.object_name for obj in objects]
    
    assert len(all_files) == 3, "Должно быть 3 файла"
    
    # Получаем список файлов в поддиректории
    objects = await loop.run_in_executor(None, lambda: list(client.list_objects(test_bucket, prefix="subdir/", recursive=True)))
    subdir_files = [obj.object_name for obj in objects]
    
    assert len(subdir_files) == 1, "Должен быть 1 файл в поддиректории"
    assert subdir_files[0] == "subdir/test3.txt"

@pytest.mark.asyncio
async def test_storage_utils_file_metadata(test_bucket):
    """Тест получения метаданных файла"""
    data = b"test data for metadata"
    key = "test_metadata.txt"
    
    # Загружаем файл
    await storage_utils.upload_file(
        test_bucket,
        key,
        data,
        content_type="text/plain"
    )
    
    # Получаем метаданные
    metadata = await storage_utils.get_file_metadata(test_bucket, key)
    assert metadata["size"] == len(data), "Размер файла должен совпадать"
    assert metadata["content_type"] == "text/plain", "Content-Type должен совпадать"
    assert "last_modified" in metadata, "Должна быть дата последнего изменения"
    assert "etag" in metadata, "Должен быть ETag"

@pytest.mark.asyncio
async def test_storage_utils_presigned_url_expiration(test_bucket):
    """Тест срока действия presigned URL"""
    data = b"test data for presigned url"
    key = "test_presigned.txt"
    
    # Загружаем файл
    await storage_utils.upload_file(test_bucket, key, data)
    
    # Генерируем URL с разным временем жизни
    url_1h = await storage_utils.generate_presigned_url(test_bucket, key, expires=3600)
    url_1d = await storage_utils.generate_presigned_url(test_bucket, key, expires=86400)
    
    assert url_1h != url_1d, "URL с разным временем жизни должны отличаться"

@pytest.mark.asyncio
async def test_storage_utils_content_type(test_bucket):
    """Тест загрузки файлов с разными content-type"""
    test_cases = [
        ("test.txt", b"text data", "text/plain"),
        ("test.jpg", b"image data", "image/jpeg"),
        ("test.json", b'{"key": "value"}', "application/json")
    ]
    
    for key, data, content_type in test_cases:
        await storage_utils.upload_file(test_bucket, key, data, content_type=content_type)
        metadata = await storage_utils.get_file_metadata(test_bucket, key)
        assert metadata["content_type"] == content_type, f"Content-Type должен быть {content_type}"

@pytest.mark.asyncio
async def test_storage_utils_error_handling(test_bucket):
    """Тест обработки ошибок"""
    # Попытка скачать несуществующий файл
    with pytest.raises(Exception):
        await storage_utils.download_file(test_bucket, "non_existent.txt")
    # Попытка удалить несуществующий файл — MinIO не выбрасывает ошибку
    await storage_utils.delete_file(test_bucket, "non_existent.txt")
    # Попытка получить метаданные несуществующего файла
    with pytest.raises(Exception):
        await storage_utils.get_file_metadata(test_bucket, "non_existent.txt") 