"""
Исключения для системы аватаров
Выделено из app/core/exceptions.py для соблюдения правила ≤500 строк
"""
from typing import Optional, Dict, Any
from uuid import UUID
from .base_exceptions import BaseServiceError, BaseValidationErrorclass AvatarError(BaseServiceError):
    """
    Базовая ошибка системы аватаров
    
    Используется для общих ошибок работы с аватарами
    """
    
    def __init__(
        self, 
        message: str,
        avatar_id: Optional[UUID] = None,
        user_id: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            service_name="Avatar",
            message=message,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.avatar_id = avatar_id
        self.user_id = user_id
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.avatar_id:
            parts.append(f"Avatar: {self.avatar_id}")
        
        if self.user_id:
            parts.append(f"User: {self.user_id}")
        
        return " | ".join(parts)class AvatarTrainingError(AvatarError):
    """
    Ошибка обучения аватара
    
    Используется для ошибок процесса обучения аватаров через FAL AI
    """
    
    def __init__(
        self, 
        message: str,
        avatar_id: Optional[UUID] = None,
        user_id: Optional[int] = None,
        training_stage: Optional[str] = None,
        fal_request_id: Optional[str] = None,
        training_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            avatar_id=avatar_id,
            user_id=user_id,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.training_stage = training_stage
        self.fal_request_id = fal_request_id
        self.training_type = training_type
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.training_type:
            parts.append(f"Type: {self.training_type}")
        
        if self.training_stage:
            parts.append(f"Stage: {self.training_stage}")
        
        if self.fal_request_id:
            parts.append(f"FAL Request: {self.fal_request_id}")
        
        return " | ".join(parts)class AvatarValidationError(BaseValidationError):
    """
    Ошибка валидации аватара
    
    Используется для ошибок валидации данных аватара и фотографий
    """
    
    def __init__(
        self, 
        field_name: Optional[str],
        message: str,
        avatar_id: Optional[UUID] = None,
        photo_id: Optional[UUID] = None,
        validation_rule: Optional[str] = None,
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
        self.avatar_id = avatar_id
        self.photo_id = photo_id
        self.validation_rule = validation_rule
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.avatar_id:
            parts.append(f"Avatar: {self.avatar_id}")
        
        if self.photo_id:
            parts.append(f"Photo: {self.photo_id}")
        
        if self.validation_rule:
            parts.append(f"Rule: {self.validation_rule}")
        
        return " | ".join(parts)class AvatarPhotoError(AvatarError):
    """
    Ошибка работы с фотографиями аватара
    
    Используется для ошибок загрузки, обработки и валидации фотографий
    """
    
    def __init__(
        self, 
        message: str,
        avatar_id: Optional[UUID] = None,
        photo_id: Optional[UUID] = None,
        file_name: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            avatar_id=avatar_id,
            error_code=error_code,
            details=details,
            cause=cause
        )
        self.photo_id = photo_id
        self.file_name = file_name
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.photo_id:
            parts.append(f"Photo: {self.photo_id}")
        
        if self.file_name:
            parts.append(f"File: {self.file_name}")
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        return " | ".join(parts)class AvatarStateError(AvatarError):
    """
    Ошибка состояния аватара
    
    Используется когда аватар находится в неподходящем состоянии для операции
    """
    
    def __init__(
        self, 
        message: str,
        avatar_id: Optional[UUID] = None,
        current_status: Optional[str] = None,
        required_status: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            avatar_id=avatar_id,
            error_code=error_code,
            details=details
        )
        self.current_status = current_status
        self.required_status = required_status
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        if self.current_status:
            parts.append(f"Current: {self.current_status}")
        
        if self.required_status:
            parts.append(f"Required: {self.required_status}")
        
        return " | ".join(parts)class AvatarNotFoundError(AvatarError):
    """
    Ошибка отсутствия аватара
    
    Используется когда запрашиваемый аватар не найден
    """
    
    def __init__(
        self, 
        avatar_id: UUID,
        user_id: Optional[int] = None,
        context: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Avatar {avatar_id} not found"
        if context:
            message += f" in {context}"
        
        super().__init__(
            message=message,
            avatar_id=avatar_id,
            user_id=user_id,
            error_code=error_code,
            details=details
        )
        self.context = contextclass AvatarPermissionError(AvatarError):
    """
    Ошибка прав доступа к аватару
    
    Используется когда пользователь не имеет прав на операцию с аватаром
    """
    
    def __init__(
        self, 
        message: str,
        avatar_id: Optional[UUID] = None,
        user_id: Optional[int] = None,
        required_permission: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            avatar_id=avatar_id,
            user_id=user_id,
            error_code=error_code,
            details=details
        )
        self.required_permission = required_permission
        self.operation = operation
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        
        if self.required_permission:
            parts.append(f"Required: {self.required_permission}")
        
        return " | ".join(parts)
