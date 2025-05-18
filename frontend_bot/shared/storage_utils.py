import os
import asyncio
from minio import Minio
from minio.error import S3Error
from typing import Optional

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

_client: Optional[Minio] = None

def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
    return _client

async def upload_file(bucket: str, key: str, data: bytes) -> str:
    client = get_minio_client()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: client.put_object(bucket, key, io.BytesIO(data), len(data))
    )
    return f"/{bucket}/{key}"

async def download_file(bucket: str, key: str) -> bytes:
    client = get_minio_client()
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.get_object(bucket, key)
    )
    data = response.read()
    response.close()
    response.release_conn()
    return data

async def delete_file(bucket: str, key: str) -> None:
    client = get_minio_client()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: client.remove_object(bucket, key)
    )

async def generate_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    client = get_minio_client()
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(
        None,
        lambda: client.presigned_get_object(bucket, key, expires=expires)
    )
    return url

import io 