"""
Модели данных для системы генерации изображений
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, JSON, String
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class GenerationStatus(str, Enum):
    """Статус генерации изображения"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StyleCategory(Base):
    """Категория стилей для генерации"""
    __tablename__ = "style_categories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    subcategories: Mapped[List["StyleSubcategory"]] = relationship(
        "StyleSubcategory", 
        back_populates="category",
        cascade="all, delete-orphan"
    )

class StyleSubcategory(Base):
    """Подкатегория стилей"""
    __tablename__ = "style_subcategories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(50), ForeignKey("style_categories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    category: Mapped["StyleCategory"] = relationship(
        "StyleCategory", 
        back_populates="subcategories"
    )
    templates: Mapped[List["StyleTemplate"]] = relationship(
        "StyleTemplate", 
        back_populates="subcategory",
        cascade="all, delete-orphan"
    )

class StyleTemplate(Base):
    """Шаблон стиля для генерации"""
    __tablename__ = "style_templates"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    subcategory_id: Mapped[str] = mapped_column(String(50), ForeignKey("style_subcategories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(String(1000), nullable=False)
    preview_url: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    subcategory: Mapped["StyleSubcategory"] = relationship(
        "StyleSubcategory", 
        back_populates="templates"
    )
    generations: Mapped[List["ImageGeneration"]] = relationship(
        "ImageGeneration", 
        back_populates="template"
    )
    favorites: Mapped[List["UserFavoriteTemplate"]] = relationship(
        "UserFavoriteTemplate", 
        back_populates="template",
        cascade="all, delete-orphan"
    )

class ImageGeneration(Base):
    """Генерация изображения пользователем"""
    __tablename__ = "image_generations"
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"))
    avatar_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("avatars.id"))  # Теперь опциональный для Imagen 4
    template_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("style_templates.id"))
    
    # 🆕 Типизация генерации
    generation_type: Mapped[str] = mapped_column(String(50), default="avatar")  # "avatar" | "imagen4" | "video"
    source_model: Mapped[Optional[str]] = mapped_column(String(100))  # "fal-ai/imagen4/preview" и т.д.
    
    # Промпты
    original_prompt: Mapped[str] = mapped_column(String(1000), nullable=False)
    final_prompt: Mapped[str] = mapped_column(String(5000), nullable=False)
    
    # Настройки генерации
    quality_preset: Mapped[str] = mapped_column(String(50), default="balanced")
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="1:1")
    num_images: Mapped[int] = mapped_column(Integer, default=1)
    
    # Результат генерации
    status: Mapped[GenerationStatus] = mapped_column(SQLEnum(GenerationStatus, native_enum=False))
    result_urls: Mapped[List[str]] = mapped_column(JSON, default=list)
    generation_time: Mapped[Optional[float]] = mapped_column(Float)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Метаданные обработки и генерации
    prompt_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Пользовательские действия
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=True)  # По умолчанию сохраняем
    
    # Связи
    user: Mapped["User"] = relationship("User")
    avatar: Mapped["Avatar"] = relationship("Avatar")
    template: Mapped[Optional["StyleTemplate"]] = relationship("StyleTemplate")

class UserFavoriteTemplate(Base):
    """Избранные шаблоны пользователя"""
    __tablename__ = "user_favorite_templates"
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"))
    template_id: Mapped[str] = mapped_column(String(50), ForeignKey("style_templates.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    template: Mapped["StyleTemplate"] = relationship("StyleTemplate", back_populates="favorites")
    
    # Уникальность пары пользователь-шаблон
    __table_args__ = (
        {"schema": None},  # Используем схему по умолчанию
    )
