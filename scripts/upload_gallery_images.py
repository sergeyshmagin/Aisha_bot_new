"""Скрипт для загрузки демо-изображений в MinIO."""

import os
from pathlib import Path
from minio import Minio
from frontend_bot.config import settings

def upload_gallery_images():
    """Загрузить демо-изображения в MinIO."""
    # Инициализация клиента MinIO
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    
    # Создаем бакет для галереи, если его нет
    bucket_name = "gallery"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")
    
    # Путь к демо-изображениям
    demo_dir = Path("assets/demo/gallery")
    demo_images = {
        "woman_morning.jpg": demo_dir / "woman_morning.jpg",
        "woman_evening.jpg": demo_dir / "woman_evening.jpg",
    }
    
    # Загружаем изображения
    for image_name, local_path in demo_images.items():
        if local_path.exists():
            client.fput_object(
                bucket_name,
                f"gallery/{image_name}",
                str(local_path)
            )
            print(f"Uploaded {image_name}")
        else:
            print(f"Warning: {local_path} not found")

if __name__ == "__main__":
    upload_gallery_images() 