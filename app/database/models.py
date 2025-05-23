"""
Модели базы данных
"""
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, BigInteger, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


# Новые Enums для аватаров
class AvatarGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AvatarStatus(str, Enum):
    DRAFT = "draft"                    # Черновик (создается)
    PHOTOS_UPLOADING = "uploading"     # Загрузка фотографий
    READY_FOR_TRAINING = "ready"       # Готов к обучению
    TRAINING = "training"              # Обучается
    COMPLETED = "completed"            # Обучение завершено
    ERROR = "error"                    # Ошибка
    CANCELLED = "cancelled"            # Отменен


class AvatarType(str, Enum):
    CHARACTER = "character"            # Персонаж
    STYLE = "style"                   # Стиль
    CUSTOM = "custom"                 # Кастомный


class PhotoValidationStatus(str, Enum):
    PENDING = "pending"               # Ожидает валидации
    VALID = "valid"                   # Валидно
    INVALID = "invalid"               # Невалидно
    DUPLICATE = "duplicate"           # Дубликат


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
    avatars: Mapped[list["Avatar"]] = relationship(back_populates="user", cascade="all, delete-orphan")
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
    """Модель аватара с расширенным функционалом для FAL AI"""
    __tablename__ = "avatars"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    # Основная информация
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[AvatarGender] = mapped_column(SQLEnum(AvatarGender))
    avatar_type: Mapped[AvatarType] = mapped_column(SQLEnum(AvatarType), default=AvatarType.CHARACTER)
    status: Mapped[AvatarStatus] = mapped_column(SQLEnum(AvatarStatus), default=AvatarStatus.DRAFT)
    
    # FAL AI интеграция
    finetune_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    training_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    training_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Настройки обучения
    fal_mode: Mapped[str] = mapped_column(String(20), default="character")  # character, style, custom
    fal_iterations: Mapped[int] = mapped_column(Integer, default=500)
    fal_priority: Mapped[str] = mapped_column(String(20), default="quality")  # quality, speed, balanced
    trigger_word: Mapped[str] = mapped_column(String(50), default="TOK")
    lora_rank: Mapped[int] = mapped_column(Integer, default=32)
    
    # Хранение данных
    avatar_data: Mapped[Dict] = mapped_column(JSON, default=dict)
    training_config: Mapped[Dict] = mapped_column(JSON, default=dict)
    
    # Статистика
    photos_count: Mapped[int] = mapped_column(Integer, default=0)
    generations_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy поля для совместимости
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True)
    photo_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preview_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Связи
    user: Mapped[User] = relationship(back_populates="avatars")
    photos: Mapped[list["AvatarPhoto"]] = relationship(back_populates="avatar", cascade="all, delete-orphan")


class AvatarPhoto(Base):
    """Фотография для аватара с расширенной валидацией"""
    __tablename__ = "avatar_photos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    avatar_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("avatars.id"))
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    # Хранение
    minio_key: Mapped[str] = mapped_column(String(255))  # Путь в MinIO
    file_hash: Mapped[str] = mapped_column(String(64), index=True)  # MD5/SHA для детекции дубликатов
    
    # Порядок и статус
    upload_order: Mapped[int] = mapped_column(Integer)  # Порядок загрузки
    validation_status: Mapped[PhotoValidationStatus] = mapped_column(SQLEnum(PhotoValidationStatus), default=PhotoValidationStatus.PENDING)
    
    # Метаданные файла
    file_size: Mapped[int] = mapped_column(Integer)  # Размер в байтах
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(10))  # jpg, png, webp
    
    # Валидация и качество
    has_face: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # Есть ли лицо
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Оценка качества 0-1
    validation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Ошибка валидации
    
    # Дополнительные метаданные
    photo_metadata: Mapped[Dict] = mapped_column(JSON, default=dict)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Legacy поля для совместимости
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Связи
    avatar: Mapped[Avatar] = relationship(back_populates="photos")
    user: Mapped[User] = relationship(back_populates="avatar_photos")


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

    user: Mapped[User] = relationship(back_populates="profile")


# Новая модель кэша транскрипта
class UserTranscriptCache(Base):
    """Кэш последнего транскрипта пользователя (только путь к файлу)."""
    __tablename__ = "user_transcript_cache"
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    path: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[User] = relationship()
