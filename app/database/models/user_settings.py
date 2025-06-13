"""
Модель настроек пользователя
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database.base import Base

class UserSettings(Base):
    """Настройки пользователя для генерации изображений"""
    
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Настройки размера изображения
    default_aspect_ratio = Column(String(10), nullable=False, default="1:1")  # 1:1, 3:4, 4:3, 9:16, 16:9
    
    # Настройки промптов
    auto_enhance_prompts = Column(Boolean, nullable=False, default=True)  # Автоулучшение промптов через GPT
    language_preference = Column(String(5), nullable=False, default="ru")  # ru, en
    
    # Настройки интерфейса
    show_technical_details = Column(Boolean, nullable=False, default=False)  # Показывать технические детали
    quick_generation_mode = Column(Boolean, nullable=False, default=False)  # Быстрая генерация без доп. меню
    
    # Метаданные
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, aspect_ratio={self.default_aspect_ratio})>"
    
    @classmethod
    def get_default_settings(cls) -> dict:
        """Возвращает настройки по умолчанию"""
        return {
            "default_aspect_ratio": "1:1",
            "auto_enhance_prompts": True,
            "language_preference": "ru",
            "show_technical_details": False,
            "quick_generation_mode": False
        }
    
    @classmethod
    def get_aspect_ratio_options(cls) -> dict:
        """Возвращает доступные варианты соотношения сторон"""
        return {
            "1:1": {"name": "🔲 Квадрат", "ratio": 1.0, "description": "Instagram, профили"},
            "3:4": {"name": "📱 Портрет", "ratio": 0.75, "description": "Вертикальные фото, портреты"},
            "4:3": {"name": "📷 Альбомная", "ratio": 1.33, "description": "Классическая горизонтальная"},
            "9:16": {"name": "📺 Сторис", "ratio": 0.5625, "description": "TikTok, Instagram Stories"},
            "16:9": {"name": "🎬 Кино", "ratio": 1.78, "description": "Широкоэкранная, YouTube"}
        }
    
    def to_dict(self) -> dict:
        """Конвертирует настройки в словарь"""
        return {
            "user_id": str(self.user_id),
            "default_aspect_ratio": self.default_aspect_ratio,
            "auto_enhance_prompts": self.auto_enhance_prompts,
            "language_preference": self.language_preference,
            "show_technical_details": self.show_technical_details,
            "quick_generation_mode": self.quick_generation_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
