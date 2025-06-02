"""
Исключения для конфигурации
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any
from .base_exceptions import BaseConfigurationErrorclass ConfigurationError(BaseConfigurationError):
    """
    Общая ошибка конфигурации
    
    Используется для ошибок настройки приложения,
    отсутствующих переменных окружения и т.д.
    """
    passclass DependencyError(ConfigurationError):
    """
    Ошибка зависимостей
    
    Используется когда отсутствуют необходимые зависимости
    или они неправильно настроены
    """
    
    def __init__(
        self, 
        dependency_name: str,
        message: str,
        required_version: Optional[str] = None,
        current_version: Optional[str] = None,
        installation_hint: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            config_key=dependency_name,
            message=message,
            error_code=error_code,
            details=details
        )
        self.dependency_name = dependency_name
        self.required_version = required_version
        self.current_version = current_version
        self.installation_hint = installation_hint
    
    def __str__(self) -> str:
        parts = [f"Dependency error '{self.dependency_name}': {self.message}"]
        
        if self.required_version:
            parts.append(f"Required: {self.required_version}")
        
        if self.current_version:
            parts.append(f"Current: {self.current_version}")
        
        if self.installation_hint:
            parts.append(f"Hint: {self.installation_hint}")
        
        return " | ".join(parts)class InvalidCredentialsError(ConfigurationError):
    """
    Ошибка неверных учетных данных
    
    Используется для ошибок аутентификации с внешними сервисами
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str,
        credential_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            config_key=f"{service_name}_credentials",
            message=message,
            error_code=error_code,
            details=details
        )
        self.service_name = service_name
        self.credential_type = credential_type
    
    def __str__(self) -> str:
        parts = [f"Invalid credentials for '{self.service_name}': {self.message}"]
        
        if self.credential_type:
            parts.append(f"Type: {self.credential_type}")
        
        return " | ".join(parts)class MissingEnvironmentVariableError(ConfigurationError):
    """
    Ошибка отсутствующей переменной окружения
    
    Используется когда обязательная переменная окружения не установлена
    """
    
    def __init__(
        self, 
        variable_name: str,
        description: Optional[str] = None,
        default_value: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Environment variable '{variable_name}' is not set"
        if description:
            message += f": {description}"
        
        super().__init__(
            config_key=variable_name,
            message=message,
            error_code=error_code,
            details=details
        )
        self.variable_name = variable_name
        self.description = description
        self.default_value = default_value
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.default_value:
            parts.append(f"Default: {self.default_value}")
        
        return " | ".join(parts)class InvalidConfigurationValueError(ConfigurationError):
    """
    Ошибка неверного значения конфигурации
    
    Используется когда значение конфигурации не соответствует ожиданиям
    """
    
    def __init__(
        self, 
        config_key: str,
        message: str,
        current_value: Any = None,
        expected_type: Optional[str] = None,
        allowed_values: Optional[list] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            config_key=config_key,
            message=message,
            error_code=error_code,
            details=details
        )
        self.current_value = current_value
        self.expected_type = expected_type
        self.allowed_values = allowed_values
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.current_value is not None:
            parts.append(f"Value: {self.current_value}")
        
        if self.expected_type:
            parts.append(f"Expected type: {self.expected_type}")
        
        if self.allowed_values:
            parts.append(f"Allowed: {self.allowed_values}")
        
        return " | ".join(parts)class ServiceUnavailableError(ConfigurationError):
    """
    Ошибка недоступности сервиса
    
    Используется когда внешний сервис недоступен или неправильно настроен
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str,
        service_url: Optional[str] = None,
        health_check_failed: bool = False,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            config_key=f"{service_name}_config",
            message=message,
            error_code=error_code,
            details=details
        )
        self.service_name = service_name
        self.service_url = service_url
        self.health_check_failed = health_check_failed
    
    def __str__(self) -> str:
        parts = [f"Service '{self.service_name}' unavailable: {self.message}"]
        
        if self.service_url:
            parts.append(f"URL: {self.service_url}")
        
        if self.health_check_failed:
            parts.append("Health check failed")
        
        return " | ".join(parts)
