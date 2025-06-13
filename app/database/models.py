"""
Центральный файл для импорта всех моделей базы данных.
Используется для автогенерации миграций Alembic.
"""

from app.database.base import Base

# Импортируем все модели для регистрации в метаданных
from app.database.models.user import User
from app.database.models.avatar import Avatar
from app.database.models.balance import Balance, Transaction
from app.database.models.transcript import Transcript

# Базовый класс для всех моделей
__all__ = ["Base", "User", "Avatar", "Balance", "Transaction", "Transcript"] 