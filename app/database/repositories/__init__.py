"""
Экспорт репозиториев
"""
from app.database.repositories.avatar import AvatarPhotoRepository, AvatarRepository
from app.database.repositories.balance import BalanceRepository
from app.database.repositories.state import StateRepository
from app.database.repositories.transcript import TranscriptRepository
from app.database.repositories.user import UserRepository

__all__ = [
    "UserRepository",
    "AvatarRepository",
    "AvatarPhotoRepository",
    "StateRepository",
    "BalanceRepository",
    "TranscriptRepository",
]
