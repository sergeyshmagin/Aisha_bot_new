import os
import pytest
from minio import Minio
from minio.error import S3Error
import io

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "192.168.0.4:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "test-bucket")

@pytest.fixture(scope="module")
def minio_client():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    # Проверяем доступность сервера
    try:
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
    except Exception as e:
        pytest.skip(f"MinIO server not available: {e}")
    yield client
    # Очистить bucket после тестов
    for obj in client.list_objects(MINIO_BUCKET, recursive=True):
        client.remove_object(MINIO_BUCKET, obj.object_name)


def test_upload_and_download(minio_client):
    data = b"test data for minio"
    key = "integration_test/test_file.txt"
    fileobj = io.BytesIO(data)
    minio_client.put_object(MINIO_BUCKET, key, fileobj, len(data))
    # Проверяем, что файл существует
    stat = minio_client.stat_object(MINIO_BUCKET, key)
    assert stat.size == len(data)
    # Скачиваем файл
    response = minio_client.get_object(MINIO_BUCKET, key)
    assert response.read() == data
    response.close()
    response.release_conn()


def test_delete(minio_client):
    data = b"to be deleted"
    key = "integration_test/delete_me.txt"
    fileobj = io.BytesIO(data)
    minio_client.put_object(MINIO_BUCKET, key, fileobj, len(data))
    minio_client.remove_object(MINIO_BUCKET, key)
    with pytest.raises(S3Error):
        minio_client.stat_object(MINIO_BUCKET, key)


def test_generate_presigned_url(minio_client):
    data = b"presigned url"
    key = "integration_test/presigned.txt"
    fileobj = io.BytesIO(data)
    minio_client.put_object(MINIO_BUCKET, key, fileobj, len(data))
    url = minio_client.presigned_get_object(MINIO_BUCKET, key)
    assert url.startswith("http") 