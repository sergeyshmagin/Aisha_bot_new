"""
Тесты для интеграции с MinIO
"""
import io
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


@pytest.fixture
def minio_client() -> Minio:
    """
    Фикстура для подключения к MinIO
    """
    client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False
    )
    return client


@pytest.fixture
def test_bucket_name() -> str:
    """
    Имя тестового бакета
    """
    return f"{settings.MINIO_BUCKET_AVATARS}_test"


@pytest.fixture
def setup_test_bucket(minio_client: Minio, test_bucket_name: str):
    """
    Создание и очистка тестового бакета
    """
    # Создаем бакет, если его нет
    if not minio_client.bucket_exists(test_bucket_name):
        minio_client.make_bucket(test_bucket_name)
    
    yield
    
    # Очищаем бакет после тестов
    try:
        for obj in minio_client.list_objects(test_bucket_name, recursive=True):
            minio_client.remove_object(test_bucket_name, obj.object_name)
    except S3Error:
        pass


@pytest.mark.usefixtures("setup_test_bucket")
def test_minio_connection(minio_client: Minio):
    """Тест подключения к MinIO"""
    # Act
    buckets = minio_client.list_buckets()
    
    # Assert
    assert len(buckets) > 0
    assert any(bucket.name == test_bucket_name for bucket in buckets)


@pytest.mark.usefixtures("setup_test_bucket")
def test_minio_put_get_object(minio_client: Minio, test_bucket_name: str):
    """Тест загрузки и получения объекта из MinIO"""
    # Arrange
    test_object_name = "test/test_file.txt"
    test_content = b"This is a test file content"
    content_type = "text/plain"
    
    # Act - Upload
    minio_client.put_object(
        bucket_name=test_bucket_name,
        object_name=test_object_name,
        data=io.BytesIO(test_content),
        length=len(test_content),
        content_type=content_type
    )
    
    # Act - Get
    response = minio_client.get_object(test_bucket_name, test_object_name)
    retrieved_content = response.read()
    response.close()
    response.release_conn()
    
    # Assert
    assert retrieved_content == test_content


@pytest.mark.usefixtures("setup_test_bucket")
def test_minio_list_objects(minio_client: Minio, test_bucket_name: str):
    """Тест получения списка объектов из MinIO"""
    # Arrange
    test_files = [
        ("test/file1.txt", b"Content 1"),
        ("test/file2.txt", b"Content 2"),
        ("test/subfolder/file3.txt", b"Content 3")
    ]
    
    # Upload test files
    for object_name, content in test_files:
        minio_client.put_object(
            bucket_name=test_bucket_name,
            object_name=object_name,
            data=io.BytesIO(content),
            length=len(content),
            content_type="text/plain"
        )
    
    # Act
    objects = list(minio_client.list_objects(test_bucket_name, recursive=True))
    
    # Assert
    assert len(objects) == 3
    object_names = [obj.object_name for obj in objects]
    for name, _ in test_files:
        assert name in object_names


@pytest.mark.usefixtures("setup_test_bucket")
def test_minio_remove_object(minio_client: Minio, test_bucket_name: str):
    """Тест удаления объекта из MinIO"""
    # Arrange
    test_object_name = "test/file_to_delete.txt"
    test_content = b"This file will be deleted"
    
    minio_client.put_object(
        bucket_name=test_bucket_name,
        object_name=test_object_name,
        data=io.BytesIO(test_content),
        length=len(test_content),
        content_type="text/plain"
    )
    
    # Проверяем, что файл существует
    objects_before = list(minio_client.list_objects(test_bucket_name, recursive=True))
    assert any(obj.object_name == test_object_name for obj in objects_before)
    
    # Act
    minio_client.remove_object(test_bucket_name, test_object_name)
    
    # Assert
    objects_after = list(minio_client.list_objects(test_bucket_name, recursive=True))
    assert not any(obj.object_name == test_object_name for obj in objects_after)


@pytest.mark.usefixtures("setup_test_bucket")
def test_minio_presigned_url(minio_client: Minio, test_bucket_name: str):
    """Тест создания предподписанного URL для объекта в MinIO"""
    # Arrange
    test_object_name = "test/presigned_url_test.txt"
    test_content = b"This is a test for presigned URL"
    
    minio_client.put_object(
        bucket_name=test_bucket_name,
        object_name=test_object_name,
        data=io.BytesIO(test_content),
        length=len(test_content),
        content_type="text/plain"
    )
    
    # Act
    presigned_url = minio_client.presigned_get_object(
        bucket_name=test_bucket_name,
        object_name=test_object_name,
        expires=3600  # URL действителен 1 час
    )
    
    # Assert
    assert presigned_url is not None
    assert test_bucket_name in presigned_url
    assert test_object_name in presigned_url
