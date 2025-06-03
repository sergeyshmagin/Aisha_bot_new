"""
Базовые классы для моделей базы данных
"""
from sqlalchemy.orm import DeclarativeBase, registry

# Создаем реестр маппинга
mapper_registry = registry()

class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    registry = mapper_registry
