"""
Исключения для хранения и сети
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any
from .base_exceptions import BaseServiceErrorclass StorageError(BaseServiceError):
    """
    Ошибка хранения данных
    
    Используется для ошибок работы с файловыми системами,
    базами данных, MinIO и другими системами хранения
    """
    
    def __init__(
        self, 
        message: str,
        storage_type: Optional[str] = None,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            service_name="Storage",
            message=message,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.storage_type = storage_type
        self.file_path = file_path
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.storage_type:
            parts.append(f"Storage: {self.storage_type}")
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        if self.file_path:
            parts.append(f"Path: {self.file_path}")
        
        return " | ".join(parts)class NetworkError(BaseServiceError):
    """
    Ошибка сети
    
    Используется для ошибок сетевых запросов,
    подключений к внешним API и сервисам
    """
    
    def __init__(
        self, 
        message: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            service_name="Network",
            message=message,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.url = url
        self.method = method
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.method and self.url:
            parts.append(f"{self.method} {self.url}")
        
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        
        if self.response_body:
            # Ограничиваем длину ответа для читаемости
            body = self.response_body[:200] + "..." if len(self.response_body) > 200 else self.response_body
            parts.append(f"Response: {body}")
        
        return " | ".join(parts)class TimeoutError(NetworkError):
    """
    Ошибка таймаута
    
    Специализированное исключение для ошибок превышения времени ожидания
    """
    
    def __init__(
        self, 
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        url: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            url=url,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.timeout_seconds = timeout_seconds
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        if self.timeout_seconds:
            parts.append(f"Timeout: {self.timeout_seconds}s")
        
        return " | ".join(parts)class DatabaseError(StorageError):
    """
    Ошибка базы данных
    
    Специализированное исключение для ошибок работы с БД
    """
    
    def __init__(
        self, 
        message: str,
        query: Optional[str] = None,
        table: Optional[str] = None,
        connection_info: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            storage_type="database",
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.query = query
        self.table = table
        self.connection_info = connection_info
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.table:
            parts.append(f"Table: {self.table}")
        
        if self.query:
            # Ограничиваем длину запроса
            query = self.query[:100] + "..." if len(self.query) > 100 else self.query
            parts.append(f"Query: {query}")
        
        return " | ".join(parts)class FileSystemError(StorageError):
    """
    Ошибка файловой системы
    
    Специализированное исключение для ошибок работы с файлами
    """
    
    def __init__(
        self, 
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        permissions: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            storage_type="filesystem",
            file_path=file_path,
            operation=operation,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.permissions = permissions
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.permissions:
            parts.append(f"Permissions: {self.permissions}")
        
        return " | ".join(parts)
