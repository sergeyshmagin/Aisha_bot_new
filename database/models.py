from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    __tablename__ = 'user_profile'

    user_id = Column(
        Integer, primary_key=True, autoincrement=False  # Telegram user_id
    )
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=True)
    username = Column(String(128), nullable=True)
    language_code = Column(String(8), nullable=True)
    is_premium = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
