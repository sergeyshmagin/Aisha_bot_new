"""
Модели базы данных.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
import uuid
from sqlalchemy import (
    Column, Integer, String, Numeric, ForeignKey, DateTime, 
    Enum as SQLEnum, Text, JSON, Index, Boolean, func,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.sql import text
from typing import Optional

Base = declarative_base()

class User(Base):
    """Модель пользователя."""
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    
    avatars = relationship("UserAvatar", back_populates="user", cascade="all, delete-orphan")
    transcripts = relationship("UserTranscript", back_populates="user", cascade="all, delete-orphan")
    history = relationship("UserHistory", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    states: Mapped[list["UserState"]] = relationship("UserState", back_populates="user", cascade="all, delete-orphan")
    balance = relationship("UserBalance", back_populates="user", cascade="all, delete-orphan", uselist=False)
    avatar_photos = relationship("UserAvatarPhoto", back_populates="user", cascade="all, delete-orphan")
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        """Строковое представление пользователя."""
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class UserAvatar(Base):
    """Модель аватара пользователя."""
    
    __tablename__ = "user_avatars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    photo_key = Column(String(255), nullable=False)
    preview_key = Column(String(255), nullable=False)
    avatar_data = Column(JSON, nullable=True)  # метаданные (JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_draft = Column(Integer, default=1, nullable=False)  # 1=True (draft), 0=False (final)
    
    user = relationship("User", back_populates="avatars")
    photos = relationship("UserAvatarPhoto", back_populates="avatar")
    
    def __repr__(self) -> str:
        """Строковое представление аватара."""
        return f"<UserAvatar(id={self.id}, user_id={self.user_id})>"

class UserTranscript(Base):
    """Модель транскрипта пользователя."""
    
    __tablename__ = "user_transcripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    audio_key = Column(String(255), nullable=False)
    transcript_key = Column(String(255), nullable=False)
    transcript_data = Column(JSON, nullable=True)  # метаданные (JSON)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="transcripts")
    
    def __repr__(self) -> str:
        """Строковое представление транскрипта."""
        return f"<UserTranscript(id={self.id}, user_id={self.user_id})>"

class UserHistory(Base):
    """Модель истории пользователя."""
    
    __tablename__ = "user_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_key = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="history")
    
    def __repr__(self) -> str:
        """Строковое представление истории."""
        return f"<UserHistory(id={self.id}, user_id={self.user_id})>"

class TransactionType(str, Enum):
    """Типы транзакций."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class Transaction(Base):
    """Модель транзакции."""
    
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    type = Column(String(50), nullable=False)  # credit/debit
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self) -> str:
        """Строковое представление транзакции."""
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount})>"

class UserState(Base):
    """Модель для хранения состояний пользователя."""
    __tablename__ = 'user_states'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete='CASCADE'), nullable=False, unique=True)
    state_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text('now()'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text('now()'), nullable=False)

    # Отношения
    user: Mapped["User"] = relationship('User', back_populates='states')

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_states_user_id"),
    )

    def __repr__(self) -> str:
        """Строковое представление состояния."""
        return f"<UserState(id={self.id}, user_id={self.user_id})>"

class UserBalance(Base):
    """Модель баланса пользователя."""
    
    __tablename__ = "user_balances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    coins = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="balance")
    
    def __repr__(self) -> str:
        """Строковое представление баланса."""
        return f"<UserBalance(id={self.id}, user_id={self.user_id})>"

class UserAvatarPhoto(Base):
    """Модель фото аватара пользователя."""
    
    __tablename__ = "user_avatar_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("user_avatars.id"), nullable=False)
    photo_key = Column(String(255), nullable=False)  # путь в MinIO
    photo_metadata = Column(JSON, nullable=True)  # метаданные фото (размер, формат и т.д.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="avatar_photos")
    avatar = relationship("UserAvatar", back_populates="photos")
    
    def __repr__(self) -> str:
        """Строковое представление фото аватара."""
        return f"<UserAvatarPhoto(id={self.id}, user_id={self.user_id}, avatar_id={self.avatar_id})>"

# Добавляем relationship в User и UserAvatar
User.avatar_photos = relationship("UserAvatarPhoto", back_populates="user")
UserAvatar.photos = relationship("UserAvatarPhoto", back_populates="avatar")

class UserProfile(Base):
    """Модель профиля пользователя."""
    __tablename__ = 'user_profiles'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    avatar_path: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text('now()'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text('now()'), onupdate=text('now()'), nullable=False
    )

    # Отношения
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"

class UserTranscriptCache(Base):
    """Кэш последнего транскрипта пользователя (только путь к файлу)."""
    __tablename__ = "user_transcript_cache"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<UserTranscriptCache(user_id={self.user_id}, path={self.path})>" 