"""
Модели базы данных
"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, BigInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aisha_v2.app.database.base import Base


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), default="ru")
    timezone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="UTC+5")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)  # Добавляем поле is_bot
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # Добавляем поле is_blocked
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    avatars: Mapped[list["Avatar"]] = relationship(back_populates="user")
    avatar_photos: Mapped[list["AvatarPhoto"]] = relationship(back_populates="user")
    balance: Mapped["UserBalance"] = relationship(back_populates="user")
    state: Mapped[Optional["UserState"]] = relationship(back_populates="user")
    transcripts: Mapped[list["UserTranscript"]] = relationship(back_populates="user")
    profile: Mapped[Optional["UserProfile"]] = relationship(back_populates="user")


class UserBalance(Base):
    """Баланс пользователя"""
    __tablename__ = "user_balances"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    coins: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    user: Mapped[User] = relationship(back_populates="balance")


class UserState(Base):
    """Состояние пользователя"""
    __tablename__ = "user_states"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    state_data: Mapped[Dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    user: Mapped[User] = relationship(back_populates="state")


class Avatar(Base):
    """Модель аватара"""
    __tablename__ = "avatars"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    # Новые поля для паритета с v1
    photo_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preview_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="avatars")
    photos: Mapped[list["AvatarPhoto"]] = relationship(back_populates="avatar")


class AvatarPhoto(Base):
    """Фотография для аватара"""
    __tablename__ = "avatar_photos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    avatar_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("avatars.id"))
    minio_key: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    # Новые поля для паритета с v1
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    photo_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    photo_hash: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)

    avatar: Mapped["Avatar"] = relationship(back_populates="photos")
    user: Mapped["User"] = relationship(back_populates="avatar_photos")


class UserTranscript(Base):
    """Модель транскрипта пользователя"""
    __tablename__ = "user_transcripts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    audio_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    transcript_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    transcript_metadata: Mapped[Dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Связи
    user: Mapped[User] = relationship(back_populates="transcripts")


# Новая модель профиля пользователя
class UserProfile(Base):
    """Модель профиля пользователя."""
    __tablename__ = 'user_profiles'

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    avatar_path: Mapped[Optional[str]] = mapped_column(String(255))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profile")


# Новая модель кэша транскрипта
class UserTranscriptCache(Base):
    """Кэш последнего транскрипта пользователя (только путь к файлу)."""
    __tablename__ = "user_transcript_cache"
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    path: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship()
