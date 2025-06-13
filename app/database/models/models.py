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

from ..base import Base

# Новые Enums для аватаров
class AvatarGender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class AvatarStatus(str, Enum):
    DRAFT = "draft"
    PHOTOS_UPLOADING = "photos_uploading"
    READY_FOR_TRAINING = "ready_for_training"
    TRAINING = "training"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"

class AvatarType(str, Enum):
    CHARACTER = "character"
    STYLE = "style"
    CUSTOM = "custom"

class AvatarTrainingType(str, Enum):
    """Тип обучения аватара (новый enum для выбора алгоритма)"""
    PORTRAIT = "portrait"
    STYLE = "style"

class FALFinetuneType(str, Enum):
    """Тип файнтюнинга FAL AI"""
    FULL = "full"
    LORA = "lora"

class FALPriority(str, Enum):
    """Приоритет обучения FAL AI"""
    SPEED = "speed"
    QUALITY = "quality"
    HIGH_RES_ONLY = "high_res_only"

class PhotoValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"

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
    settings: Mapped[Optional["UserSettings"]] = relationship(back_populates="user")
    group: Mapped[Optional["UserGroup"]] = relationship(back_populates="user")

# UserBalance теперь в отдельном файле app/database/models/user_balance.py

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
    gender: Mapped[AvatarGender] = mapped_column(SQLEnum(AvatarGender, native_enum=False))
    avatar_type: Mapped[AvatarType] = mapped_column(SQLEnum(AvatarType, native_enum=False), default=AvatarType.CHARACTER)
    training_type: Mapped[AvatarTrainingType] = mapped_column(SQLEnum(AvatarTrainingType, native_enum=False), default=AvatarTrainingType.PORTRAIT)
    status: Mapped[AvatarStatus] = mapped_column(SQLEnum(AvatarStatus, native_enum=False), default=AvatarStatus.DRAFT)
    
    # FAL AI интеграция
    finetune_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    fal_request_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)  # 🆕 Request ID для отслеживания
    training_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    training_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    training_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Настройки обучения - универсальные
    fal_mode: Mapped[str] = mapped_column(String(20), default="character")  # character, style, custom
    fal_iterations: Mapped[int] = mapped_column(Integer, default=500)
    fal_priority: Mapped[FALPriority] = mapped_column(SQLEnum(FALPriority, native_enum=False), default=FALPriority.QUALITY)
    trigger_word: Mapped[str] = mapped_column(String(50), default="TOK")
    lora_rank: Mapped[int] = mapped_column(Integer, default=32)
    
    # 🆕 Настройки обучения - специфичные для FAL AI
    learning_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Скорость обучения
    finetune_type: Mapped[FALFinetuneType] = mapped_column(SQLEnum(FALFinetuneType, native_enum=False), default=FALFinetuneType.LORA)
    finetune_comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Комментарий к обучению
    
    # 🆕 Portrait-specific настройки (flux-lora-portrait-trainer)
    trigger_phrase: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Для портретного тренера
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Шаги для портретного тренера (вместо iterations)
    multiresolution_training: Mapped[bool] = mapped_column(Boolean, default=True)  # Мультиразрешающее обучение
    subject_crop: Mapped[bool] = mapped_column(Boolean, default=True)  # Автообрезка субъекта
    create_masks: Mapped[bool] = mapped_column(Boolean, default=False)  # Создание масок
    
    # 🆕 Style-specific настройки (flux-pro-trainer)
    captioning: Mapped[bool] = mapped_column(Boolean, default=True)  # Автогенерация подписей
    
    # 🆕 Результаты обучения
    diffusers_lora_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL LoRA файла
    config_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL конфигурации
    training_logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Логи обучения
    training_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Ошибки обучения
    
    # 🆕 Webhook и отслеживание
    webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL для уведомлений
    last_status_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Последняя проверка статуса
    
    # Хранение данных
    avatar_data: Mapped[Dict] = mapped_column(JSON, default=dict)
    training_config: Mapped[Dict] = mapped_column(JSON, default=dict)
    fal_response_data: Mapped[Dict] = mapped_column(JSON, default=dict)  # 🆕 Полный ответ FAL AI
    
    # Статистика
    photos_count: Mapped[int] = mapped_column(Integer, default=0)
    generations_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Основной аватар
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)  # Основной аватар пользователя
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user: Mapped[User] = relationship(back_populates="avatars")
    photos: Mapped[list["AvatarPhoto"]] = relationship(back_populates="avatar", cascade="all, delete-orphan")

    # ✅ УНИВЕРСАЛЬНЫЕ МЕТОДЫ ДЛЯ РАБОТЫ СО СТАТУСОМ
    def is_completed(self) -> bool:
        """Проверяет, завершен ли аватар"""
        return self.status == AvatarStatus.COMPLETED
    
    def is_draft(self) -> bool:
        """Проверяет, является ли аватар черновиком"""
        return self.status == AvatarStatus.DRAFT
    
    def is_training(self) -> bool:
        """Проверяет, обучается ли аватар"""
        return self.status == AvatarStatus.TRAINING
        
    def is_ready_for_generation(self) -> bool:
        """Проверяет, готов ли аватар для генерации"""
        return self.status == AvatarStatus.COMPLETED and (self.diffusers_lora_file_url or self.finetune_id)
    
    def get_status_display(self) -> str:
        """Возвращает человекочитаемый статус"""
        status_map = {
            AvatarStatus.DRAFT: "Черновик",
            AvatarStatus.PHOTOS_UPLOADING: "Загрузка фото",
            AvatarStatus.READY_FOR_TRAINING: "Готов к обучению",
            AvatarStatus.TRAINING: "Обучается",
            AvatarStatus.COMPLETED: "Готов",
            AvatarStatus.ERROR: "Ошибка",
            AvatarStatus.CANCELLED: "Отменен"
        }
        return status_map.get(self.status, str(self.status.value))

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
    validation_status: Mapped[PhotoValidationStatus] = mapped_column(SQLEnum(PhotoValidationStatus, native_enum=False), default=PhotoValidationStatus.PENDING)
    
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

class UserGroup(Base):
    """Персональная группа пользователя для AI-функций"""
    __tablename__ = "user_groups"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    
    # Информация о группе
    group_id: Mapped[str] = mapped_column(BigInteger, unique=True, index=True)  # Telegram group ID
    group_title: Mapped[str] = mapped_column(String(255))
    invite_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Метаданные
    created_via: Mapped[str] = mapped_column(String(50), default="pool_strategy")  # pool_strategy, manual, etc
    is_forum_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    setup_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Топики группы (JSON с массивом)
    topics: Mapped[Dict] = mapped_column(JSON, default=dict)  # {"transcription": 123, "generation": 456}
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    user: Mapped[User] = relationship(back_populates="group")

    def is_accessible(self) -> bool:
        """Проверяет, доступна ли группа"""
        # Логика проверки доступности может быть расширена
        return self.setup_completed and self.group_id is not None

    def get_topic_id(self, topic_type: str) -> Optional[int]:
        """Получает ID топика по типу"""
        return self.topics.get(topic_type) if self.topics else None

    def update_topics(self, new_topics: Dict[str, int]):
        """Обновляет информацию о топиках"""
        if not self.topics:
            self.topics = {}
        self.topics.update(new_topics)
