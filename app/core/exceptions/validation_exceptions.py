"""
Исключения для валидации данных
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any, List
from .base_exceptions import BaseValidationError


class ValidationError(BaseValidationError):
    """
    Общая ошибка валидации
    
    Используется для ошибок валидации пользовательских данных,
    параметров запросов, конфигурации и т.д.
    """
    pass


class InvalidFormatError(ValidationError):
    """
    Ошибка неверного формата данных
    
    Используется когда данные не соответствуют ожидаемому формату
    """
    
    def __init__(
        self, 
        field_name: Optional[str],
        message: str,
        expected_format: Optional[str] = None,
        actual_format: Optional[str] = None,
        value: Any = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            field_name=field_name,
            message=message,
            value=value,
            error_code=error_code,
            details=details
        )
        self.expected_format = expected_format
        self.actual_format = actual_format
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.expected_format:
            parts.append(f"Expected format: {self.expected_format}")
        
        if self.actual_format:
            parts.append(f"Actual format: {self.actual_format}")
        
        return " | ".join(parts)


class InvalidParameterError(ValidationError):
    """
    Ошибка неверного параметра
    
    Используется для валидации параметров функций и методов
    """
    
    def __init__(
        self, 
        parameter_name: str,
        message: str,
        value: Any = None,
        allowed_values: Optional[List[Any]] = None,
        parameter_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            field_name=parameter_name,
            message=message,
            value=value,
            error_code=error_code,
            details=details
        )
        self.parameter_name = parameter_name
        self.allowed_values = allowed_values
        self.parameter_type = parameter_type
    
    def __str__(self) -> str:
        parts = [f"Invalid parameter '{self.parameter_name}': {self.message}"]
        
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        
        if self.parameter_type:
            parts.append(f"Type: {self.parameter_type}")
        
        if self.allowed_values:
            parts.append(f"Allowed: {self.allowed_values}")
        
        return " | ".join(parts)


class InvalidStateError(ValidationError):
    """
    Ошибка неверного состояния объекта
    
    Используется когда объект находится в состоянии,
    не позволяющем выполнить операцию
    """
    
    def __init__(
        self, 
        message: str,
        object_type: Optional[str] = None,
        object_id: Optional[str] = None,
        current_state: Optional[str] = None,
        required_state: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            field_name="state",
            message=message,
            value=current_state,
            error_code=error_code,
            details=details
        )
        self.object_type = object_type
        self.object_id = object_id
        self.current_state = current_state
        self.required_state = required_state
    
    def __str__(self) -> str:
        parts = [f"Invalid state: {self.message}"]
        
        if self.object_type and self.object_id:
            parts.append(f"Object: {self.object_type}#{self.object_id}")
        
        if self.current_state:
            parts.append(f"Current: {self.current_state}")
        
        if self.required_state:
            parts.append(f"Required: {self.required_state}")
        
        return " | ".join(parts)


class InvalidRangeError(ValidationError):
    """
    Ошибка выхода значения за допустимые пределы
    
    Используется для валидации числовых значений, размеров файлов и т.д.
    """
    
    def __init__(
        self, 
        field_name: Optional[str],
        message: str,
        value: Any = None,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            field_name=field_name,
            message=message,
            value=value,
            error_code=error_code,
            details=details
        )
        self.min_value = min_value
        self.max_value = max_value
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.min_value is not None and self.max_value is not None:
            parts.append(f"Range: {self.min_value} - {self.max_value}")
        elif self.min_value is not None:
            parts.append(f"Min: {self.min_value}")
        elif self.max_value is not None:
            parts.append(f"Max: {self.max_value}")
        
        return " | ".join(parts)


class RequiredFieldError(ValidationError):
    """
    Ошибка отсутствия обязательного поля
    
    Используется когда обязательное поле не предоставлено
    """
    
    def __init__(
        self, 
        field_name: str,
        context: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Required field '{field_name}' is missing"
        if context:
            message += f" in {context}"
        
        super().__init__(
            field_name=field_name,
            message=message,
            error_code=error_code,
            details=details
        )
        self.context = context 