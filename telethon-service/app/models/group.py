"""
Модели данных для управления группами
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TopicType(str, Enum):
    """Типы функций для персональных групп"""
    TRANSCRIPTION = "transcription"
    AVATAR_CREATION = "avatar_creation"
    GALLERY_BROWSE = "gallery_browse"
    SUPPORT = "support"


class GroupStatus(str, Enum):
    """Статусы групп в пуле"""
    AVAILABLE = "available"      # Доступна для назначения
    ASSIGNED = "assigned"        # Назначена пользователю
    CONFIGURING = "configuring"  # В процессе настройки
    ACTIVE = "active"           # Активно используется
    ERROR = "error"             # Ошибка при создании/настройке


class GroupCreateRequest(BaseModel):
    """Запрос на создание персональной группы"""
    user_id: int = Field(..., description="ID пользователя Telegram")
    topic_type: TopicType = Field(..., description="Тип функции")
    username: Optional[str] = Field(None, description="Username пользователя")
    custom_title: Optional[str] = Field(None, description="Кастомное название группы")


class GroupCreateResponse(BaseModel):
    """Ответ на создание персональной группы"""
    success: bool = Field(..., description="Успешность операции")
    group_id: Optional[int] = Field(None, description="ID созданной группы")
    group_title: Optional[str] = Field(None, description="Название группы")
    group_link: Optional[str] = Field(None, description="Ссылка-приглашение в группу")
    forum_enabled: Optional[bool] = Field(None, description="Включен ли форум")
    topic_type: Optional[TopicType] = Field(None, description="Тип функции")
    user_id: Optional[int] = Field(None, description="ID пользователя")
    created_at: Optional[datetime] = Field(None, description="Время создания")
    message: Optional[str] = Field(None, description="Сообщение о результате")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class PreCreatedGroup(BaseModel):
    """Модель предсозданной группы в пуле"""
    id: Optional[int] = Field(None, description="ID записи в БД")
    chat_id: int = Field(..., description="ID чата в Telegram")
    title: str = Field(..., description="Текущее название группы")
    invite_link: str = Field(..., description="Ссылка-приглашение")
    status: GroupStatus = Field(GroupStatus.AVAILABLE, description="Статус группы")
    topic_type: Optional[TopicType] = Field(None, description="Назначенный тип функции")
    assigned_user_id: Optional[int] = Field(None, description="ID назначенного пользователя")
    assigned_username: Optional[str] = Field(None, description="Username назначенного пользователя")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    assigned_at: Optional[datetime] = Field(None, description="Время назначения")
    configured_at: Optional[datetime] = Field(None, description="Время настройки")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class GroupInfo(BaseModel):
    """Информация о группе пользователя"""
    group_id: int = Field(..., description="ID группы")
    title: str = Field(..., description="Название группы")
    topic_type: TopicType = Field(..., description="Тип функции")
    invite_link: str = Field(..., description="Ссылка-приглашение")
    is_active: bool = Field(True, description="Активна ли группа")
    created_at: datetime = Field(..., description="Время создания")


class GroupTypesResponse(BaseModel):
    """Ответ со списком доступных типов групп"""
    topic_types: list[str] = Field(..., description="Список типов функций")
    descriptions: Dict[str, str] = Field(..., description="Описания типов функций")


class PoolStatusResponse(BaseModel):
    """Статус пула групп"""
    total_groups: int = Field(..., description="Общее количество групп в пуле")
    available_groups: int = Field(..., description="Доступных групп")
    assigned_groups: int = Field(..., description="Назначенных групп")
    active_groups: int = Field(..., description="Активных групп")
    error_groups: int = Field(..., description="Групп с ошибками")
    last_created: Optional[datetime] = Field(None, description="Время последнего создания")
    
    
class BatchCreateRequest(BaseModel):
    """Запрос на пакетное создание групп"""
    count: int = Field(..., ge=1, le=100, description="Количество групп для создания")
    topic_type: TopicType = Field(TopicType.SUPPORT, description="Тип функции для групп")
    delay_seconds: float = Field(5.0, ge=1.0, le=60.0, description="Задержка между созданиями")
    base_title: str = Field("Aisha Group", description="Базовое название группы")


class GroupStatusRequest(BaseModel):
    """Запрос статуса группы"""
    user_id: int = Field(..., description="ID пользователя")
    topic_type: Optional[TopicType] = Field(None, description="Тип функции (для фильтрации)")


class GroupStatusResponse(BaseModel):
    """Ответ со статусом групп пользователя"""
    user_id: int = Field(..., description="ID пользователя")
    groups: list[GroupInfo] = Field(..., description="Список групп пользователя")
    total_groups: int = Field(..., description="Общее количество групп")


class HealthResponse(BaseModel):
    """Ответ health check"""
    status: str = Field(..., description="Статус сервиса")
    telethon_connected: bool = Field(..., description="Подключен ли Telethon")
    service: str = Field(..., description="Название сервиса")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время проверки") 