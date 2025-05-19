"""
Настройки приложения.
"""

import os
from typing import Optional

# MinIO settings
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Avatar settings
AVATAR_MIN_PHOTOS = int(os.getenv("AVATAR_MIN_PHOTOS", "3"))
AVATAR_MAX_PHOTOS = int(os.getenv("AVATAR_MAX_PHOTOS", "10"))
AVATAR_PRICE = int(os.getenv("AVATAR_PRICE", "150"))

# Gallery settings
GALLERY_DEBOUNCE_TIMEOUT = int(os.getenv("GALLERY_DEBOUNCE_TIMEOUT", "6"))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"

if REDIS_PASSWORD:
    auth = f":{REDIS_PASSWORD}@"
else:
    auth = ""

protocol = "rediss" if REDIS_SSL else "redis"
REDIS_URL = f"{protocol}://{auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" 