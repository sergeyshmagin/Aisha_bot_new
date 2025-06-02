"""
Сервис управления обучением аватаров с FAL AI
LEGACY: Файл рефакторен в модульную структуру app/services/avatar/training_service/
Этот файл обеспечивает обратную совместимость импортов.

Удалить после тестирования новой структуры!
"""

# Импорт из новой модульной структуры
from .training_service.main_service import AvatarTrainingService

# Экспорт для обратной совместимости
__all__ = ["AvatarTrainingService"]
