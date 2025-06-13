"""
Модель промокодов
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PromokodeType(str, Enum):
    """Типы промокодов"""
    BALANCE = "balance"  # Пополнение баланса
    BONUS = "bonus"      # Бонус при пополнении
    DISCOUNT = "discount"  # Скидка на пакет


class Promokode(Base):
    """Модель промокода"""
    
    __tablename__ = "promokodes"
    
    # Основные поля
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[PromokodeType] = mapped_column(String(20), nullable=False)
    
    # Значения
    balance_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Для type=balance
    bonus_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # Для type=bonus  
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Для type=discount
    
    # Ограничения использования
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = без ограничений
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_uses_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Лимит на пользователя
    
    # Временные ограничения
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Метаданные
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Кто создал
    
    # Системные поля
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Связи
    usages: Mapped[list["PromokodeUsage"]] = relationship(
        "PromokodeUsage", 
        back_populates="promokode",
        cascade="all, delete-orphan"
    )
    
    # Индексы
    __table_args__ = (
        Index("idx_promokode_code", "code"),
        Index("idx_promokode_type", "type"),
        Index("idx_promokode_active", "is_active"),
        Index("idx_promokode_valid", "valid_from", "valid_until"),
    )
    
    def is_valid(self) -> bool:
        """Проверяет, валиден ли промокод"""
        if not self.is_active:
            return False
            
        now = datetime.now(timezone.utc)
        
        # Проверяем временные рамки
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
            
        # Проверяем лимит использований
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
            
        return True
    
    def can_be_used_by_user(self, user_id: UUID) -> bool:
        """Проверяет, может ли пользователь использовать промокод"""
        if not self.is_valid():
            return False
            
        # Проверяем лимит на пользователя
        if self.max_uses_per_user:
            user_uses = len([u for u in self.usages if u.user_id == user_id])
            if user_uses >= self.max_uses_per_user:
                return False
                
        return True


class PromokodeUsage(Base):
    """Использование промокода"""
    
    __tablename__ = "promokode_usages"
    
    # Основные поля
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    promokode_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("promokodes.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Детали использования
    amount_added: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Сколько добавлено
    bonus_added: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # Бонус добавлен
    package_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Какой пакет использован
    
    # Системные поля
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Связи
    promokode: Mapped[Promokode] = relationship("Promokode", back_populates="usages")
    user: Mapped["User"] = relationship("User")
    
    # Индексы
    __table_args__ = (
        Index("idx_promokode_usage_user", "user_id"),
        Index("idx_promokode_usage_code", "promokode_id"),
        Index("idx_promokode_usage_date", "used_at"),
    ) 