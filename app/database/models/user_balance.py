"""
Модель баланса пользователя
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserBalance(Base):
    """Модель баланса пользователя"""
    
    __tablename__ = "user_balances"
    
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    coins: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Связь с пользователем
    user: Mapped["User"] = relationship(back_populates="balance")
    
    def __repr__(self):
        return f"<UserBalance(user_id={self.user_id}, coins={self.coins})>" 