#!/usr/bin/env python3
"""
Pytest тесты для компонентов системы аватаров
"""
import pytest
import sys
from pathlib import Path
from uuid import uuid4

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestAvatarServices:
    """Тесты сервисов аватаров"""

    @pytest.mark.asyncio
    async def test_fal_training_service(self):
        """Тест FAL Training Service"""
        from app.services.avatar.fal_training_service import FALTrainingService
        
        service = FALTrainingService()
        config = service.get_config_summary()
        
        # Проверяем базовую конфигурацию
        assert 'test_mode' in config
        assert 'webhook_url' in config
        assert 'supported_training_types' in config
        
        # Проверяем поддерживаемые типы обучения
        supported_types = config['supported_training_types']
        assert 'portrait' in supported_types
        assert 'style' in supported_types
        
        # Тест получения информации о типах обучения
        for training_type in ["portrait", "style"]:
            info = service.get_training_type_info(training_type)
            assert 'name' in info
            assert 'description' in info
            assert len(info['name']) > 0
            assert len(info['description']) > 0
        
        # Тест симуляции обучения
        avatar_id = uuid4()
        request_id = await service.start_avatar_training(
            avatar_id=avatar_id,
            training_type="portrait",
            training_data_url="https://test.example.com/data.zip"
        )
        
        assert request_id is not None
        assert len(request_id) > 0
        
        # Тест проверки статуса
        status = await service.check_training_status(request_id, "portrait")
        assert status is not None
        assert 'status' in status

    @pytest.mark.asyncio
    async def test_redis_service(self):
        """Тест Redis Service"""
        from app.services.avatar.redis_service import AvatarRedisService
        
        service = AvatarRedisService()
        test_user_id = 12345
        test_photo_data = b"fake_photo_data_for_testing"
        test_meta = {
            "file_id": "test_file_123",
            "width": 512,
            "height": 512,
            "timestamp": "2025-05-23T16:00:00Z"
        }
        
        try:
            # Тест буферизации фото
            success = await service.buffer_photo(test_user_id, test_photo_data, test_meta)
            assert success is True
            
            # Получение информации о буфере
            buffer_info = await service.get_buffer_info(test_user_id)
            assert 'count' in buffer_info
            assert buffer_info['count'] >= 1
            
            # Получение фото из буфера
            photos = await service.get_buffered_photos(test_user_id)
            assert len(photos) >= 1
            
            # Тест блокировок
            lock_token = await service.acquire_avatar_lock(test_user_id, "create")
            assert lock_token is not None
            
            if lock_token:
                released = await service.release_avatar_lock(test_user_id, lock_token, "create")
                assert released is True
            
        finally:
            # Очистка
            await service.clear_photo_buffer(test_user_id)
            await service.close()

class TestAvatarUI:
    """Тесты UI компонентов аватаров"""

    def test_avatar_texts(self):
        """Тест текстов аватаров"""
        from app.texts.avatar import TRAINING_TYPE_TEXTS
        
        required_keys = [
            "selection_menu",
            "portrait_info", 
            "style_info",
            "detailed_comparison",
            "training_type_saved"
        ]
        
        for key in required_keys:
            assert key in TRAINING_TYPE_TEXTS, f"Отсутствует ключ: {key}"
            text = TRAINING_TYPE_TEXTS[key]
            assert len(text) > 0, f"Пустой текст для ключа: {key}"
        
        # Тест форматирования
        test_text = TRAINING_TYPE_TEXTS["training_type_saved"].format(type_name="Портретный")
        assert "Портретный" in test_text

    def test_avatar_keyboards(self):
        """Тест клавиатур аватаров"""
        from app.keyboards.avatar import (
            get_training_type_keyboard,
            get_training_type_confirmation_keyboard,
            get_comparison_keyboard,
            get_avatar_gender_keyboard
        )
        
        # Тест основных клавиатур
        keyboards = [
            ("Выбор типа обучения", get_training_type_keyboard()),
            ("Подтверждение портретного", get_training_type_confirmation_keyboard("portrait")),
            ("Подтверждение художественного", get_training_type_confirmation_keyboard("style")),
            ("Сравнение типов", get_comparison_keyboard()),
            ("Выбор пола", get_avatar_gender_keyboard()),
        ]
        
        for name, keyboard in keyboards:
            assert hasattr(keyboard, 'inline_keyboard'), f"Некорректная клавиатура: {name}"
            button_count = sum(len(row) for row in keyboard.inline_keyboard)
            assert button_count > 0, f"Пустая клавиатура: {name}"

    def test_avatar_states(self):
        """Тест состояний аватаров"""
        from app.handlers.state import AvatarStates
        
        # Проверяем новые состояния для выбора типа обучения
        required_states = [
            "selecting_training_type",
            "viewing_training_info", 
            "viewing_training_comparison",
            "selecting_gender",
            "entering_name"
        ]
        
        for state_name in required_states:
            assert hasattr(AvatarStates, state_name), f"Отсутствует состояние: {state_name}"

class TestAvatarConfiguration:
    """Тесты конфигурации аватаров"""

    def test_avatar_config(self):
        """Тест конфигурации"""
        from app.core.config import settings
        
        # Проверяем критические настройки
        assert hasattr(settings, 'FAL_TRAINING_TEST_MODE')
        assert hasattr(settings, 'FAL_WEBHOOK_URL')
        assert hasattr(settings, 'AVATAR_MIN_PHOTOS')
        assert hasattr(settings, 'AVATAR_MAX_PHOTOS')
        
        # Проверяем значения
        assert settings.AVATAR_MIN_PHOTOS > 0
        assert settings.AVATAR_MAX_PHOTOS >= settings.AVATAR_MIN_PHOTOS
        
        # Проверяем пресеты (если существуют)
        preset_names = ["FAL_PRESET_FAST", "FAL_PRESET_BALANCED", "FAL_PRESET_QUALITY"]
        existing_presets = [name for name in preset_names if hasattr(settings, name)]
        
        # Если есть пресеты, проверяем их структуру
        for preset_name in existing_presets:
            preset = getattr(settings, preset_name)
            assert isinstance(preset, dict), f"Пресет {preset_name} должен быть словарем"

class TestAvatarModels:
    """Тесты моделей аватаров"""

    def test_avatar_enums(self):
        """Тест enum типов аватаров"""
        from app.database.models import (
            AvatarTrainingType, AvatarType, AvatarGender, AvatarStatus
        )
        
        # Проверяем enum типы обучения
        training_types = list(AvatarTrainingType)
        assert len(training_types) == 2, f"Ожидалось 2 типа обучения, получено: {len(training_types)}"
        
        # Проверяем, что есть PORTRAIT и STYLE
        expected_types = {AvatarTrainingType.PORTRAIT, AvatarTrainingType.STYLE}
        assert set(training_types) == expected_types, f"Неожиданные типы обучения: {training_types}"
        
        # Проверяем соответствие enum значений
        assert AvatarTrainingType.PORTRAIT.value == "portrait"
        assert AvatarTrainingType.STYLE.value == "style"

    def test_avatar_model_structure(self):
        """Тест структуры модели Avatar"""
        from app.database.models import Avatar
        
        # Проверяем атрибуты модели Avatar
        required_attrs = ['training_type', 'avatar_type', 'gender', 'status', 'name']
        
        for attr in required_attrs:
            assert hasattr(Avatar, attr), f"Отсутствует атрибут Avatar.{attr}"
        
        # Проверяем метаданные таблицы
        avatar_table = Avatar.__table__
        column_names = {col.name for col in avatar_table.columns}
        
        # Базовые поля
        basic_fields = {'id', 'user_id', 'name', 'gender', 'status'}
        missing_basic = basic_fields - column_names
        assert not missing_basic, f"Отсутствуют базовые поля: {missing_basic}"

class TestAvatarIntegration:
    """Интеграционные тесты системы аватаров"""
    
    @pytest.mark.asyncio 
    async def test_avatar_workflow_components(self):
        """Тест интеграции компонентов workflow аватаров"""
        # Проверяем что все основные компоненты могут быть импортированы
        try:
            from app.services.avatar.fal_training_service import FALTrainingService
            from app.services.avatar.redis_service import AvatarRedisService
            from app.texts.avatar import TRAINING_TYPE_TEXTS
            from app.keyboards.avatar import get_training_type_keyboard
            from app.handlers.state import AvatarStates
            from app.database.models import Avatar, AvatarTrainingType
            
            # Проверяем совместимость enum значений с текстами
            for training_type in AvatarTrainingType:
                type_value = training_type.value
                assert f"{type_value}_info" in TRAINING_TYPE_TEXTS, f"Нет текста для типа {type_value}"
            
            # Проверяем что сервисы могут работать с enum значениями
            service = FALTrainingService()
            for training_type in AvatarTrainingType:
                info = service.get_training_type_info(training_type.value)
                assert info is not None
                
        except ImportError as e:
            pytest.fail(f"Ошибка импорта компонентов: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 