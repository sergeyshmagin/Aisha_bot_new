"""
Константы для ресурсов приложения
"""

# Базы данных
class DatabaseNames:
    """Имена баз данных"""
    MAIN = "aisha_v2"  # Основная база данных
    TEST = "aisha_v2_test"  # Тестовая база данных# Redis
class RedisConfig:
    """Конфигурация Redis"""
    DEFAULT_DB = 0
    SESSION_DB = 1
    CACHE_DB = 2
    QUEUE_DB = 3
    
    # Префиксы ключей
    KEY_PREFIXES = {
        "user_state": "aisha:v2:state:",
        "user_session": "aisha:v2:session:",
        "avatar_cache": "aisha:v2:avatar:",
        "rate_limit": "aisha:v2:ratelimit:",
    }
    
    # TTL (в секундах)
    TTL = {
        "user_state": 3600,  # 1 час
        "user_session": 86400,  # 24 часа
        "avatar_cache": 1800,  # 30 минут
        "rate_limit": 60,  # 1 минута
    }# MinIO
class MinioConfig:
    """Конфигурация MinIO"""
    BUCKET_NAMES = {
        "avatars": "aisha-v2-avatars",
        "photos": "aisha-v2-photos",
        "temp": "aisha-v2-temp",
    }
    
    FOLDERS = {
        "original": "original/",
        "processed": "processed/",
        "generated": "generated/",
        "temp": "temp/",
    }
    
    # Время жизни временных файлов (в днях)
    TEMP_FILE_EXPIRY = 1
    
    # Максимальные размеры файлов (в байтах)
    MAX_SIZES = {
        "photo": 5 * 1024 * 1024,  # 5MB
        "avatar": 10 * 1024 * 1024,  # 10MB
    }# Очереди
class QueueNames:
    """Имена очередей"""
    PHOTO_PROCESSING = "aisha:v2:photo:processing"
    AVATAR_TRAINING = "aisha:v2:avatar:training"
    AVATAR_GENERATION = "aisha:v2:avatar:generation"
    NOTIFICATIONS = "aisha:v2:notifications"# Лимиты API
class ApiLimits:
    """Лимиты API"""
    # Количество запросов в минуту
    RATE_LIMITS = {
        "default": 60,
        "photo_upload": 10,
        "avatar_generate": 5,
    }
    
    # Таймауты (в секундах)
    TIMEOUTS = {
        "default": 30,
        "photo_processing": 60,
        "avatar_training": 300,
        "avatar_generation": 120,
    }# Настройки кэширования
class CacheConfig:
    """Настройки кэширования"""
    # Время жизни кэша (в секундах)
    TTL = {
        "user_profile": 300,  # 5 минут
        "avatar_list": 60,  # 1 минута
        "photo_list": 60,  # 1 минута
        "statistics": 1800,  # 30 минут
    }
    
    # Префиксы ключей
    KEY_PREFIXES = {
        "user": "cache:v2:user:",
        "avatar": "cache:v2:avatar:",
        "photo": "cache:v2:photo:",
        "stats": "cache:v2:stats:",
        "transcript": "cache:v2:transcript:",
        "audio": "cache:v2:audio:",
    }
