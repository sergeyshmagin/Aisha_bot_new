import logging
from uuid import UUID

logger = logging.getLogger(__name__)

def safe_uuid(val):
    """
    Безопасно преобразует строку в UUID. Если невалидно — возвращает None и логирует ошибку.
    """
    try:
        return UUID(str(val))
    except Exception as e:
        logger.error(f"Некорректный UUID: {val} ({e})")
        return None
