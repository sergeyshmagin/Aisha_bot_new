"""
Экспорт репозиториев
"""
from aisha_v2.app.database.repositories.avatar import AvatarPhotoRepository, AvatarRepository
from aisha_v2.app.database.repositories.balance import BalanceRepository
from aisha_v2.app.database.repositories.state import StateRepository
from aisha_v2.app.database.repositories.transcript import TranscriptRepository
from aisha_v2.app.database.repositories.user import UserRepository

__all__ = [
    "UserRepository",
    "AvatarRepository",
    "AvatarPhotoRepository",
    "StateRepository",
    "BalanceRepository",
    "TranscriptRepository",
]
