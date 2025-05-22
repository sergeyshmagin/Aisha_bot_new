"""
Утилиты для тестов.
"""

import asyncio
from typing import Any, Callable, Coroutine
from functools import wraps
import uuid
from datetime import datetime
from typing import Dict, Any

from database.models import (
    UserAvatar, UserTranscript, Transaction, UserHistory
)


def async_test(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
    """
    Декоратор для асинхронных тестов.
    
    Args:
        func: Асинхронная функция для тестирования.
    
    Returns:
        Синхронная функция-обертка.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Синхронная обертка для асинхронной функции."""
        return asyncio.run(func(*args, **kwargs))
    return wrapper


def create_test_user(
    telegram_id: int = 123456789,
    first_name: str = "Test",
    last_name: str = "User",
    username: str = "testuser",
    language_code: str = "ru"
) -> Dict[str, Any]:
    """Создает тестовые данные пользователя."""
    return {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "language_code": language_code,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_test_state(
    user_id: uuid.UUID,
    state: str = "test",
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Создает тестовые данные состояния пользователя."""
    if data is None:
        data = {"key": "value"}
    return {
        "user_id": user_id,
        "state_data": {
            "state": state,
            "data": data
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_test_balance(
    user_id: uuid.UUID,
    coins: float = 100.0
) -> Dict[str, Any]:
    """Создает тестовые данные баланса пользователя."""
    return {
        "user_id": user_id,
        "coins": coins,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_test_avatar(
    user_id: uuid.UUID,
    original_path: str = "/path/to/original.jpg",
    processed_path: str = "/path/to/processed.jpg",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Создает тестовые данные аватара пользователя."""
    if metadata is None:
        metadata = {"size": 1024, "format": "jpg"}
    return {
        "user_id": user_id,
        "avatar_data": {
            "original_path": original_path,
            "processed_path": processed_path,
            "metadata": metadata
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_test_transcript(
    user_id: uuid.UUID,
    original_path: str = "/path/to/audio.mp3",
    transcript_path: str = "/path/to/transcript.txt",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Создает тестовые данные транскрипта пользователя."""
    if metadata is None:
        metadata = {"duration": 60, "format": "mp3"}
    return {
        "user_id": user_id,
        "transcript_data": {
            "original_path": original_path,
            "transcript_path": transcript_path,
            "metadata": metadata
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def create_test_transaction(
    user_id: uuid.UUID,
    amount: float = 100.0,
    type: str = "credit",
    description: str = "Test transaction"
) -> Dict[str, Any]:
    """Создает тестовые данные транзакции."""
    return {
        "user_id": user_id,
        "amount": amount,
        "type": type,
        "description": description,
        "created_at": datetime.utcnow()
    }


def create_test_history(
    user_id: uuid.UUID,
    action_type: str = "test_action",
    action_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Создает тестовые данные истории пользователя."""
    if action_data is None:
        action_data = {"key": "value"}
    return {
        "user_id": user_id,
        "action_type": action_type,
        "action_data": action_data,
        "created_at": datetime.utcnow()
    }


def create_test_message(user_id: int, text: str, message_type: str = "text") -> dict:
    """
    Создает тестовое сообщение.
    
    Args:
        user_id: ID пользователя.
        text: Текст сообщения.
        message_type: Тип сообщения.
    
    Returns:
        Словарь с данными сообщения.
    """
    return {
        "user_id": user_id,
        "text": text,
        "message_type": message_type
    } 