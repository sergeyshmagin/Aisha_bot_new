"""
Базовые исключения для иерархии
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any


class BaseAppError(Exception):
    """
    Базовое исключение приложения
    
    Все кастомные исключения должны наследоваться от этого класса
    для единообразной обработки ошибок
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует исключение в словарь для логирования"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


class BaseServiceError(BaseAppError):
    """
    Базовое исключение для сервисов
    
    Используется для ошибок в бизнес-логике сервисов
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, error_code, details, cause)
        self.service_name = service_name
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        return f"[{self.service_name}] {base_msg}"


class BaseValidationError(BaseAppError):
    """
    Базовое исключение для валидации
    
    Используется для ошибок валидации данных
    """
    
    def __init__(
        self, 
        field_name: Optional[str],
        message: str, 
        value: Any = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.field_name = field_name
        self.value = value
    
    def __str__(self) -> str:
        if self.field_name:
            return f"Validation error in '{self.field_name}': {self.message}"
        return f"Validation error: {self.message}"


class BaseConfigurationError(BaseAppError):
    """
    Базовое исключение для конфигурации
    
    Используется для ошибок конфигурации приложения
    """
    
    def __init__(
        self, 
        config_key: Optional[str],
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.config_key = config_key
    
    def __str__(self) -> str:
        if self.config_key:
            return f"Configuration error for '{self.config_key}': {self.message}"
        return f"Configuration error: {self.message}" 