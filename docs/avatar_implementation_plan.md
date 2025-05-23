# План реализации системы аватаров

## 📋 Обзор

Этот план описывает поэтапную реализацию системы аватаров, адаптированную из архивной версии (`archive/aisha_v1`) с учетом современных требований и интеграции с FAL AI.

## 🎯 Этапы реализации

### Этап 0: Выбор типа обучения аватара (Приоритет: HIGH) 🆕

#### 0.1 UI/UX для выбора типа аватара

**Новый этап в workflow создания аватара**:
```
Выбор типа аватара → Выбор пола → Ввод имени → Загрузка фото → Обучение
```

**Создать**: `app/handlers/avatar/training_type_selection.py`
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar import get_training_type_keyboard
from app.texts.avatar import TRAINING_TYPE_TEXTS

router = Router()

@router.callback_query(F.data == "select_training_type")
async def show_training_type_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор типа обучения аватара"""
    
    text = TRAINING_TYPE_TEXTS["selection_menu"]
    keyboard = get_training_type_keyboard()
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard
    )
    await state.set_state(AvatarStates.selecting_training_type)

@router.callback_query(F.data.startswith("training_type_"))
async def select_training_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа обучения"""
    
    training_type = callback.data.split("_", 2)[2]  # portrait, style, etc.
    
    # Сохраняем выбор в состоянии
    await state.update_data(training_type=training_type)
    
    # Показываем детальную информацию о выбранном типе
    text = TRAINING_TYPE_TEXTS[f"{training_type}_info"]
    keyboard = get_training_type_confirmation_keyboard(training_type)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("confirm_training_"))
async def confirm_training_type(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора типа обучения и переход к выбору пола"""
    
    training_type = callback.data.split("_", 2)[2]
    await state.update_data(training_type=training_type)
    
    # Переход к выбору пола (существующий обработчик)
    from .create import show_gender_selection
    await show_gender_selection(callback, state)
```

#### 0.2 Клавиатуры для выбора типа обучения

**Дополнить**: `app/keyboards/avatar.py`
```python
def get_training_type_keyboard():
    """Клавиатура выбора типа обучения аватара"""
    
    keyboard = InlineKeyboardBuilder()
    
    # Портретный тип (рекомендуемый)
    keyboard.row(
        InlineKeyboardButton(
            text="🎭 Портретный ⭐ (Рекомендуется)",
            callback_data="training_type_portrait"
        )
    )
    
    # Универсальный тип
    keyboard.row(
        InlineKeyboardButton(
            text="🎨 Художественный",
            callback_data="training_type_style"
        )
    )
    
    # Сравнение типов
    keyboard.row(
        InlineKeyboardButton(
            text="📊 Сравнить типы",
            callback_data="compare_training_types"
        )
    )
    
    # Назад
    keyboard.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_avatar_menu"
        )
    )
    
    return keyboard.as_markup()

def get_training_type_confirmation_keyboard(training_type: str):
    """Клавиатура подтверждения выбора типа обучения"""
    
    keyboard = InlineKeyboardBuilder()
    
    # Подтверждение
    keyboard.row(
        InlineKeyboardButton(
            text="✅ Выбрать этот тип",
            callback_data=f"confirm_training_{training_type}"
        )
    )
    
    # Посмотреть другой тип
    other_type = "style" if training_type == "portrait" else "portrait"
    other_name = "Художественный" if training_type == "portrait" else "Портретный"
    
    keyboard.row(
        InlineKeyboardButton(
            text=f"🔄 Посмотреть {other_name}",
            callback_data=f"training_type_{other_type}"
        )
    )
    
    # Сравнение
    keyboard.row(
        InlineKeyboardButton(
            text="📊 Подробное сравнение",
            callback_data="detailed_comparison"
        )
    )
    
    # Назад к выбору
    keyboard.row(
        InlineKeyboardButton(
            text="◀️ К выбору типа",
            callback_data="select_training_type"
        )
    )
    
    return keyboard.as_markup()

def get_comparison_keyboard():
    """Клавиатура для сравнения типов обучения"""
    
    keyboard = InlineKeyboardBuilder()
    
    # Выбор после сравнения
    keyboard.row(
        InlineKeyboardButton(
            text="🎭 Выбрать Портретный",
            callback_data="confirm_training_portrait"
        ),
        InlineKeyboardButton(
            text="🎨 Выбрать Художественный", 
            callback_data="confirm_training_style"
        )
    )
    
    # Назад
    keyboard.row(
        InlineKeyboardButton(
            text="◀️ К выбору типа",
            callback_data="select_training_type"
        )
    )
    
    return keyboard.as_markup()
```

#### 0.3 Тексты для объяснения типов обучения

**Дополнить**: `app/texts/avatar.py`
```python
TRAINING_TYPE_TEXTS = {
    "selection_menu": """
🎯 **Выберите тип обучения аватара**

Для получения лучших результатов выберите подходящий тип обучения:

🎭 **Портретный** ⭐ - Специально для лиц людей
🎨 **Художественный** - Универсальный для стилей

💡 **Совет**: Для фотографий людей выбирайте Портретный тип
""",

    "portrait_info": """
🎭 **Портретный тип обучения** ⭐

**Лучший выбор для портретов с высокой детализацией!**

✅ **Преимущества:**
• Специально оптимизирован для лиц
• Автоматическая обрезка портретов  
• Создание масок для точности
• Быстрое обучение (3-15 минут)
• Превосходное качество портретов

🎯 **Идеально для:**
• Селфи и фотографии людей
• Портретная съемка
• Профессиональные фото
• Личные аватары

⚡ **Скорость**: Очень быстро
🎨 **Качество для портретов**: Максимальное

*Технология: Flux LoRA Portrait Trainer*
""",

    "style_info": """
🎨 **Художественный тип обучения**

**Универсальное решение для любого контента!**

✅ **Преимущества:**
• Поддержка любых стилей и объектов
• Гибкие настройки обучения
• Автоматическое создание описаний
• Различные режимы качества
• Максимальная универсальность

🎯 **Идеально для:**
• Художественные стили
• Предметы и объекты  
• Архитектура и интерьеры
• Абстрактные концепции
• Нестандартные задачи

⚡ **Скорость**: Средняя
🎨 **Универсальность**: Максимальная

*Технология: Flux Pro Trainer*
""",

    "detailed_comparison": """
📊 **Подробное сравнение типов обучения**

| Критерий | 🎭 Портретный | 🎨 Художественный |
|----------|---------------|-------------------|
| **Лучше для** | Лица людей | Стили, объекты |
| **Скорость** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Качество портретов** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Универсальность** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Простота** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

🎯 **Рекомендации:**

**Выбирайте Портретный**, если:
• У вас фотографии людей
• Нужно высокое качество лиц
• Хотите быстрый результат

**Выбирайте Художественный**, если:  
• Нужны стили или объекты
• Требуется максимальная гибкость
• Работаете с нестандартным контентом

💡 **90% пользователей выбирают Портретный тип**
""",

    "training_type_saved": """
✅ **Тип обучения выбран!**

{type_name} - отличный выбор для ваших задач.

Теперь давайте настроим основные параметры аватара.
"""
}
```

#### 0.4 Обновление состояний FSM

**Дополнить**: `app/core/states.py`
```python
class AvatarStates(StatesGroup):
    # Выбор типа обучения (новые состояния)
    selecting_training_type = State()     # Выбор типа обучения
    viewing_training_info = State()       # Просмотр информации о типе
    viewing_training_comparison = State() # Сравнение типов
    
    # Создание
    selecting_type = State()      # Выбор типа аватара
    selecting_gender = State()    # Выбор пола
    waiting_name = State()        # Ввод имени
    
    # Загрузка фото
    uploading_photos = State()    # Загрузка фотографий
    confirming_photos = State()   # Подтверждение фото
    selecting_quality = State()   # Выбор качества обучения 🆕
    
    # Обучение
    configuring_training = State() # Настройка обучения
    training_in_progress = State() # Процесс обучения
    
    # Просмотр
    viewing_gallery = State()     # Просмотр галереи
    viewing_avatar = State()      # Просмотр аватара
```

### Этап 1: Доработка базовых сервисов (Приоритет: HIGH)

#### 1.1 Обновление AvatarService
**Файл**: `app/services/avatar_db.py`

**Задачи**:
- ✅ Базовая структура уже существует
- 🔄 Добавить поддержку training_type
- 🔄 Интегрировать с новой моделью данных

**Новые методы для добавления**:
```python
async def set_avatar_training_type(self, avatar_id: UUID, training_type: str) -> bool:
    """Устанавливает тип обучения аватара (portrait/style)"""
    
async def get_optimal_training_settings(self, avatar_id: UUID) -> Dict:
    """Возвращает оптимальные настройки обучения на основе типа аватара"""
    
async def finalize_avatar_creation(self, avatar_id: UUID) -> bool:
    """Завершает создание аватара, меняет статус с DRAFT на PHOTOS_UPLOADING"""
    
async def cancel_avatar_creation(self, avatar_id: UUID) -> bool:
    """Отменяет создание аватара и очищает связанные данные"""
    
async def get_avatar_statistics(self, avatar_id: UUID) -> Dict:
    """Возвращает статистику аватара (количество фото, прогресс обучения и т.д.)"""
    
async def set_avatar_main(self, user_id: int, avatar_id: UUID) -> bool:
    """Устанавливает аватар как основной для пользователя"""
```

#### 1.2 Создание FAL AI Training Service 🆕
**Создать**: `app/services/avatar/fal_training_service.py`

```python
from typing import Dict, Any, Optional
import asyncio
import logging
from uuid import UUID

from app.core.config import settings
from .fal_portrait_trainer import FALPortraitTrainer
from .fal_trainer_adapter import FALTrainerAdapter, FALModelType

logger = logging.getLogger(__name__)

class FALTrainingService:
    """Сервис для обучения аватаров через FAL AI с автовыбором модели"""
    
    def __init__(self):
        self.portrait_trainer = FALPortraitTrainer()
        self.adapter = FALTrainerAdapter()
        self.test_mode = settings.FAL_TRAINING_TEST_MODE
    
    async def start_avatar_training(
        self, 
        avatar_id: UUID,
        training_type: str,  # "portrait" или "style"
        training_data_url: str,
        user_preferences: Optional[Dict] = None
    ) -> str:
        """
        Запускает обучение аватара с автоматическим выбором оптимальной модели
        
        Args:
            avatar_id: ID аватара
            training_type: Тип обучения (portrait/style)
            training_data_url: URL к архиву с фотографиями
            user_preferences: Пользовательские настройки (speed/balanced/quality)
            
        Returns:
            request_id или finetune_id для отслеживания
        """
        try:
            # 🧪 ТЕСТОВЫЙ РЕЖИМ - имитация обучения без реальных запросов
            if self.test_mode:
                return await self._simulate_training(avatar_id, training_type)
            
            # Получаем настройки качества
            quality_preset = user_preferences.get("quality", "balanced")
            settings_preset = self._get_quality_preset(quality_preset)
            
            # Генерируем уникальный триггер
            trigger = f"TOK_{avatar_id.hex[:8]}"
            
            # Настраиваем webhook с типом обучения
            webhook_url = self._get_webhook_url(training_type)
            
            if training_type == "portrait":
                # Используем специализированный портретный тренер
                preset = settings_preset["portrait"]
                
                result = await self.portrait_trainer.train_avatar_async(
                    images_data_url=training_data_url,
                    trigger_phrase=trigger,
                    steps=preset["steps"],
                    learning_rate=preset["learning_rate"],
                    subject_crop=True,
                    create_masks=True,
                    multiresolution_training=True,
                    webhook_url=webhook_url
                )
                
                logger.info(f"Портретное обучение запущено для аватара {avatar_id}: {result}")
                return result
                
            else:
                # Используем универсальный тренер
                model_type = FALModelType.STYLE if training_type == "style" else FALModelType.GENERAL
                preset = settings_preset["general"]
                
                result = await self.adapter.train_avatar(
                    model_type=model_type,
                    images_data_url=training_data_url,
                    trigger_word=trigger,
                    iterations=preset["iterations"],
                    learning_rate=preset["learning_rate"],
                    priority=preset.get("priority", "quality"),
                    webhook_url=webhook_url
                )
                
                logger.info(f"Универсальное обучение запущено для аватара {avatar_id}: {result}")
                return result.get("finetune_id") or result.get("request_id")
                
        except Exception as e:
            logger.exception(f"Ошибка при запуске обучения аватара {avatar_id}: {e}")
            raise
    
    async def _simulate_training(self, avatar_id: UUID, training_type: str) -> str:
        """
        🧪 Имитация обучения для тестового режима
        """
        import uuid
        mock_request_id = f"test_{avatar_id.hex[:8]}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🧪 ТЕСТ РЕЖИМ: Имитация обучения {training_type} для аватара {avatar_id}")
        logger.info(f"🧪 Сгенерирован тестовый request_id: {mock_request_id}")
        
        # Имитируем задержку
        await asyncio.sleep(1)
        
        # Через некоторое время можно вызвать webhook с тестовыми данными
        if settings.FAL_WEBHOOK_URL:
            asyncio.create_task(self._simulate_webhook_callback(
                mock_request_id, 
                avatar_id, 
                training_type
            ))
        
        return mock_request_id
    
    async def _simulate_webhook_callback(
        self, 
        request_id: str, 
        avatar_id: UUID, 
        training_type: str
    ):
        """
        🧪 Имитация webhook callback для тестового режима
        """
        import aiohttp
        
        # Задержка перед "завершением" обучения
        await asyncio.sleep(30)  # 30 секунд для тестирования
        
        webhook_data = {
            "request_id": request_id,
            "avatar_id": str(avatar_id),
            "training_type": training_type,
            "status": "completed",
            "result": {
                "test_mode": True,
                "mock_model_url": f"https://test.example.com/models/{request_id}.safetensors"
            }
        }
        
        try:
            webhook_url = self._get_webhook_url(training_type)
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_data) as response:
                    logger.info(f"🧪 Тестовый webhook отправлен: {response.status}")
        except Exception as e:
            logger.warning(f"🧪 Ошибка отправки тестового webhook: {e}")
    
    def _get_webhook_url(self, training_type: str) -> Optional[str]:
        """
        Формирует URL webhook с учетом типа обучения
        """
        if not settings.FAL_WEBHOOK_URL:
            return None
            
        base_url = settings.FAL_WEBHOOK_URL
        
        # Добавляем параметр типа обучения
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}training_type={training_type}"
    
    async def check_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Проверяет статус обучения"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return await self._simulate_status_check(request_id, training_type)
            
            if training_type == "portrait":
                return await self.portrait_trainer.check_training_status(request_id)
            else:
                # Для универсального тренера - адаптер не имеет этого метода,
                # используем прямое обращение к FAL API
                import fal_client
                return fal_client.status("fal-ai/flux-pro-trainer", request_id, with_logs=True)
                
        except Exception as e:
            logger.exception(f"Ошибка проверки статуса {request_id}: {e}")
            raise
    
    async def _simulate_status_check(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """🧪 Имитация проверки статуса для тестового режима"""
        
        # Простая логика: если запрос "новый" - в процессе, если "старый" - завершен
        import time
        current_time = time.time()
        request_time = int(request_id.split('_')[-1], 16) if request_id.startswith("test_") else 0
        
        if current_time - request_time < 60:  # Меньше минуты - в процессе
            return {
                "status": "in_progress",
                "progress": min(80, int((current_time - request_time) * 2)),
                "logs": [f"🧪 Тестовое обучение {training_type} в процессе..."]
            }
        else:
            return {
                "status": "completed",
                "progress": 100,
                "logs": [f"🧪 Тестовое обучение {training_type} завершено!"]
            }
    
    async def get_training_result(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Получает результат обучения"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return {
                    "test_mode": True,
                    "request_id": request_id,
                    "training_type": training_type,
                    "mock_model_url": f"https://test.example.com/models/{request_id}.safetensors",
                    "diffusers_lora_file": {
                        "url": f"https://test.example.com/models/{request_id}.safetensors",
                        "file_name": f"test_model_{training_type}.safetensors"
                    }
                }
            
            if training_type == "portrait":
                return await self.portrait_trainer.get_training_result(request_id)
            else:
                import fal_client
                return fal_client.result("fal-ai/flux-pro-trainer", request_id)
                
        except Exception as e:
            logger.exception(f"Ошибка получения результата {request_id}: {e}")
            raise
    
    def _get_quality_preset(self, quality: str) -> Dict[str, Any]:
        """Возвращает настройки качества из конфигурации"""
        presets = {
            "fast": settings.FAL_PRESET_FAST,
            "balanced": settings.FAL_PRESET_BALANCED,
            "quality": settings.FAL_PRESET_QUALITY
        }
        return presets.get(quality, settings.FAL_PRESET_BALANCED)
    
    def get_training_type_info(self, training_type: str) -> Dict[str, Any]:
        """Возвращает информацию о типе обучения"""
        
        info = {
            "portrait": {
                "name": "Портретный",
                "description": "Специально для фотографий людей",
                "speed": "⭐⭐⭐⭐ (3-15 минут)",
                "quality_portraits": "⭐⭐⭐⭐⭐",
                "best_for": ["Селфи", "Портреты", "Фото людей"],
                "technology": "Flux LoRA Portrait Trainer"
            },
            "style": {
                "name": "Художественный", 
                "description": "Универсальный для любого контента",
                "speed": "⭐⭐⭐ (5-30 минут)",
                "quality_portraits": "⭐⭐⭐⭐",
                "best_for": ["Стили", "Объекты", "Архитектура"],
                "technology": "Flux Pro Trainer"
            }
        }
        
        return info.get(training_type, info["portrait"])
```

#### 1.3 Создание PhotoService 
**Файл**: `app/services/avatar/photo_service.py` (уже существует)

**Задачи**:
- 🔄 Адаптировать методы из архивной версии
- 🔄 Добавить продвинутую валидацию
- 🔄 Интегрировать дедупликацию

### Этап 2: Доработка обработчиков (Приоритет: HIGH)

#### 2.1 Рефакторинг основного обработчика
**Файл**: `app/handlers/avatar.py` (уже существует)

**Задачи**:
- 🔄 Интегрировать выбор типа обучения в workflow
- 🔄 Разделить на модули по примеру архивной версии
- 🔄 Добавить недостающие обработчики

**Новая структура workflow**:
```
1. Главное меню → Создать аватар
2. Выбор типа обучения (portrait/style) 🆕
3. Просмотр информации о выбранном типе 🆕
4. Подтверждение выбора типа 🆕
5. Выбор пола аватара
6. Ввод имени
7. Загрузка фотографий
8. Подтверждение и запуск обучения
```

#### 2.2 Создание модульных обработчиков

**Создать**: `app/handlers/avatar/__init__.py`
```python
from .training_type_selection import router as training_type_router
from .create import router as create_router
from .gallery import router as gallery_router
from .photo_upload import router as upload_router

__all__ = [
    "training_type_router", 
    "create_router", 
    "gallery_router", 
    "upload_router"
]
```

**Обновить**: `app/handlers/avatar/create.py` 
```python
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.services.avatar_db import AvatarService
from app.services.avatar.fal_training_service import FALTrainingService
from app.core.constants import AvatarType, AvatarGender

router = Router()

@router.callback_query(F.data == "create_avatar")
async def start_avatar_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания аватара с выбора типа обучения"""
    
    # Переходим к выбору типа обучения
    from .training_type_selection import show_training_type_selection
    await show_training_type_selection(callback, state)

@router.callback_query(F.data.startswith("avatar_type_"))
async def select_avatar_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа аватара (после выбора типа обучения)"""
    
    avatar_type = callback.data.split("_", 2)[2]
    await state.update_data(avatar_type=avatar_type)
    
    # Продолжаем к выбору пола
    await show_gender_selection(callback, state)

async def show_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор пола аватара"""
    
    data = await state.get_data()
    training_type = data.get("training_type", "portrait")
    
    text = f"""
🎯 **Выберите пол аватара**

Тип обучения: {training_type.title()}
Это поможет настроить оптимальные параметры генерации.
"""
    
    keyboard = get_avatar_gender_keyboard()
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard
    )
    await state.set_state(AvatarStates.selecting_gender)
```

### Этап 3: Система состояний FSM (Приоритет: MEDIUM)

#### 3.1 Обновление состояний аватаров
**Файл**: `app/core/states.py` (обновить существующий раздел)

```python
from aiogram.fsm.state import State, StatesGroup

class AvatarStates(StatesGroup):
    # Выбор типа обучения (новые состояния)
    selecting_training_type = State()     # Выбор типа обучения
    viewing_training_info = State()       # Просмотр информации о типе
    viewing_training_comparison = State() # Сравнение типов
    
    # Создание
    selecting_type = State()      # Выбор типа аватара
    selecting_gender = State()    # Выбор пола
    waiting_name = State()        # Ввод имени
    
    # Загрузка фото
    uploading_photos = State()    # Загрузка фотографий
    confirming_photos = State()   # Подтверждение фото
    selecting_quality = State()   # Выбор качества обучения 🆕
    
    # Обучение
    configuring_training = State() # Настройка обучения
    training_in_progress = State() # Процесс обучения
    
    # Просмотр
    viewing_gallery = State()     # Просмотр галереи
    viewing_avatar = State()      # Просмотр аватара
```

### Этап 4: Валидация и безопасность (Приоритет: HIGH)

#### 4.1 Создание валидатора фото
**Создать**: `app/services/avatar/photo_validator.py`
```python
# Адаптировать из archive/aisha_v1/frontend_bot/services/avatar_validator.py
# с учетом типа обучения

class PhotoValidator:
    """Валидатор фотографий для аватаров с учетом типа обучения"""
    
    def __init__(self):
        self.portrait_requirements = {
            "min_face_size": 100,
            "require_face": True,
            "min_resolution": 512,
            "max_photos": 50,
            "min_photos": 5
        }
        
        self.style_requirements = {
            "min_face_size": 0,
            "require_face": False,
            "min_resolution": 256,
            "max_photos": 100,
            "min_photos": 10
        }
    
    async def validate_photo(
        self, 
        photo_data: bytes, 
        training_type: str = "portrait"
    ) -> ValidationResult:
        """Валидация фото с учетом типа обучения"""
        
        requirements = (
            self.portrait_requirements 
            if training_type == "portrait" 
            else self.style_requirements
        )
        
        # Базовая валидация
        basic_result = await self._validate_basic(photo_data)
        if not basic_result.is_valid:
            return basic_result
        
        # Специфичная валидация для типа
        if training_type == "portrait":
            return await self._validate_portrait(photo_data, requirements)
        else:
            return await self._validate_style(photo_data, requirements)
```

### Этап 5: Интеграция с MinIO (Приоритет: MEDIUM)

#### 5.1 Адаптация клиента MinIO
**Файл**: `app/services/storage/minio.py` (уже существует)

**Задачи**:
- 🔄 Добавить поддержку разных типов аватаров
- 🔄 Структурировать хранение по типам

**Обновленная структура хранения**:
```
avatars/
├── user_{user_id}/
│   ├── avatar_{avatar_id}/
│   │   ├── meta.json              # Включает training_type
│   │   ├── photos/
│   │   │   ├── original/
│   │   │   ├── thumbnails/
│   │   │   └── processed/
│   │   ├── training_data/
│   │   │   ├── portrait_set.zip   # Для портретного типа
│   │   │   └── style_set.zip      # Для художественного типа
│   │   └── results/
│   │       ├── portrait_model/
│   │       └── style_model/
```

### Этап 6: Клавиатуры и тексты (Приоритет: MEDIUM)

#### 6.1 Обновление клавиатур
**Файл**: `app/keyboards/avatar.py` (дополнить существующий)

**Новые клавиатуры из раздела 0.2** (уже описаны выше)

#### 6.2 Обновление текстов
**Файл**: `app/texts/avatar.py` (дополнить существующий)

**Новые тексты из раздела 0.3** (уже описаны выше)

### Этап 7: Тестирование (Приоритет: HIGH)

#### 7.1 Unit тесты
**Создать**: `tests/test_avatar_training_types.py`
```python
# Тесты для выбора типов обучения
class TestTrainingTypeSelection:
    async def test_portrait_type_selection(self):
        """Тест выбора портретного типа"""
        
    async def test_style_type_selection(self):
        """Тест выбора художественного типа"""
        
    async def test_training_type_comparison(self):
        """Тест сравнения типов обучения"""

class TestFALTrainingService:
    async def test_portrait_training_start(self):
        """Тест запуска портретного обучения"""
        
    async def test_style_training_start(self):
        """Тест запуска художественного обучения"""
        
    async def test_quality_presets(self):
        """Тест пресетов качества"""
```

## 📋 Обновленные конкретные задачи

### 🔥 Немедленные задачи (0-3 дня)

1. **🧪 Настроить тестовый режим обучения** 🆕 (КРИТИЧНО)
   - Цель: Безопасная отладка без трат на FAL AI
   - Файлы: 
     - `app/core/config.py` - добавить настройки отладки
     - `app/services/avatar/fal_training_service.py` - реализовать mock режим
     - `.env.example` - документировать переменные
   - Результат: `FAL_TRAINING_TEST_MODE=true` полностью имитирует обучение

2. **🔗 Настроить единый webhook для всех типов обучения** 🆕
   - Цель: Обработка уведомлений от портретного и универсального тренеров
   - Файлы:
     - `app/api/webhooks/fal_training.py` - создать webhook обработчик
     - URL: `https://aibots.kz/api/avatar/status_update?training_type=portrait`
     - URL: `https://aibots.kz/api/avatar/status_update?training_type=style`
   - Результат: Один endpoint различает типы по query параметру

3. **🎛️ Создать UI для выбора типа обучения**
   - Файл: `app/handlers/avatar/training_type_selection.py`
   - Клавиатуры: `app/keyboards/avatar.py` (дополнить)
   - Тексты: `app/texts/avatar.py` (дополнить)

4. **🤖 Создать FALTrainingService с mock режимом**
   - Файл: `app/services/avatar/fal_training_service.py`
   - Автовыбор модели + полная имитация для отладки
   - Поддержка webhook simulation

### 📅 Краткосрочные задачи (3-7 дней)

5. **🧪 Протестировать тестовый режим**
   - Проверить полный цикл: создание → "обучение" → webhook → завершение
   - Убедиться, что никаких реальных запросов к FAL AI не отправляется
   - Логирование всех mock операций

6. **📊 Добавить мониторинг и логирование**
   - Детальные логи для режима отладки
   - Метрики по типам обучения
   - Алерты при ошибках webhook'ов

7. **🔧 Обновить workflow создания аватара**
   - Интегрировать выбор типа обучения в существующий процесс
   - Обновить состояния FSM

### 📆 Среднесрочные задачи (1-2 недели)

8. **🚀 Подготовка к продакшну**
   - Тестирование с реальными API ключами FAL AI
   - Переключение `FAL_TRAINING_TEST_MODE=false`
   - Мониторинг расходов на обучение

9. **📈 Аналитика и оптимизация**
   - Отслеживание популярности типов обучения
   - A/B тестирование рекомендаций
   - Оптимизация настроек качества

## 🧪 Критически важные моменты для отладки

### ✅ Безопасность разработки
```python
# В тестовом режиме НИКАКИХ реальных запросов к FAL AI!
if settings.FAL_TRAINING_TEST_MODE:
    logger.info("🧪 ТЕСТ РЕЖИМ: Имитация обучения")
    return await self._simulate_training(avatar_id, training_type)
```

### ✅ Webhook конфигурация
```bash
# Для портретного обучения
https://aibots.kz/api/avatar/status_update?training_type=portrait

# Для художественного обучения  
https://aibots.kz/api/avatar/status_update?training_type=style
```

### ✅ Переменные окружения
```bash
# Обязательно в .env для разработки!
FAL_TRAINING_TEST_MODE=true  # Не тратит деньги
FAL_MOCK_TRAINING_DURATION=30  # Быстрое тестирование
FAL_ENABLE_WEBHOOK_SIMULATION=true  # Тестовые webhook'и
```

## 🔧 Ответы на вопросы

### 1. **Тестовый режим для отладки** ✅
- **Решение**: `FAL_TRAINING_TEST_MODE=true` в config
- **Поведение**: Полная имитация обучения без реальных API запросов
- **Webhook**: Даже тестовые webhook'и будут отправляться для проверки логики
- **Логи**: `🧪` эмодзи для всех тестовых операций

### 2. **Webhook для разных типов обучения** ✅
- **Решение**: Один endpoint с query параметром
- **URL**: `https://aibots.kz/api/avatar/status_update?training_type={portrait|style}`
- **Преимущества**: 
  - Единая логика обработки
  - Простая маршрутизация
  - Легко различать типы
- **Альтернатива**: Можно добавить отдельные endpoints в будущем если потребуется

### 3. **Безопасность расходов** ✅
- Тестовый режим по умолчанию включен (`true`)
- Реальные запросы только при явном `FAL_TRAINING_TEST_MODE=false`
- Подробное логирование всех операций
- Mock data для полного тестирования UX

**Готово к реализации!** 🚀 

#### 1.3 Обновление конфигурации для отладки 🧪

**Дополнить**: `app/core/config.py`

```python
# FAL AI - Debug & Development Settings 🧪
FAL_TRAINING_TEST_MODE: bool = Field(True, env="FAL_TRAINING_TEST_MODE")  # ✅ Уже есть
FAL_WEBHOOK_URL: str = Field("https://aibots.kz/api/avatar/status_update", env="FAL_WEBHOOK_URL")  # ✅ Уже есть

# Новые настройки для отладки
FAL_MOCK_TRAINING_DURATION: int = Field(30, env="FAL_MOCK_TRAINING_DURATION")  # секунд
FAL_ENABLE_WEBHOOK_SIMULATION: bool = Field(True, env="FAL_ENABLE_WEBHOOK_SIMULATION")
FAL_TEST_REQUEST_PREFIX: str = Field("test_", env="FAL_TEST_REQUEST_PREFIX")

# Webhook endpoints для разных типов (опционально)
FAL_WEBHOOK_PORTRAIT_URL: Optional[str] = Field(None, env="FAL_WEBHOOK_PORTRAIT_URL")
FAL_WEBHOOK_STYLE_URL: Optional[str] = Field(None, env="FAL_WEBHOOK_STYLE_URL")
```

#### 1.4 Создание webhook обработчика

**Создать**: `app/api/webhooks/fal_training.py`

```python
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

from app.services.avatar_db import AvatarService
from app.services.avatar.training_service import TrainingService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/avatar/status_update")
async def fal_training_webhook(request: Request):
    """
    Webhook для получения обновлений статуса обучения от FAL AI
    Поддерживает как портретный, так и универсальный тренеры
    """
    try:
        data = await request.json()
        
        # Определяем тип обучения из параметров запроса или payload
        training_type = request.query_params.get("training_type", "portrait")
        
        request_id = data.get("request_id")
        status = data.get("status")
        avatar_id = data.get("avatar_id")
        
        logger.info(f"Получен webhook от FAL AI: {training_type}, {status}, avatar_id={avatar_id}")
        
        # Обновляем статус аватара в базе данных
        avatar_service = AvatarService()
        training_service = TrainingService()
        
        if status == "completed":
            # Обучение завершено успешно
            result = data.get("result", {})
            
            if training_type == "portrait":
                model_url = result.get("diffusers_lora_file", {}).get("url")
            else:
                model_url = result.get("finetune_id")
            
            await avatar_service.complete_avatar_training(
                avatar_id=avatar_id,
                model_url=model_url,
                training_data=result
            )
            
            # Уведомляем пользователя (через Telegram)
            await training_service.notify_training_completed(avatar_id, training_type)
            
        elif status == "failed":
            # Обучение провалилось
            error_message = data.get("error", "Неизвестная ошибка")
            
            await avatar_service.fail_avatar_training(
                avatar_id=avatar_id,
                error_message=error_message
            )
            
            await training_service.notify_training_failed(avatar_id, error_message)
            
        elif status == "in_progress":
            # Обучение в процессе
            progress = data.get("progress", 0)
            
            await avatar_service.update_avatar_training_progress(
                avatar_id=avatar_id,
                progress=progress
            )
        
        return {"status": "ok", "message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.exception(f"Ошибка обработки webhook FAL AI: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/avatar/training_status/{request_id}")
async def get_training_status(request_id: str, training_type: str = "portrait"):
    """
    API для ручной проверки статуса обучения (для отладки)
    """
    try:
        fal_service = FALTrainingService()
        status = await fal_service.check_training_status(request_id, training_type)
        
        return {
            "request_id": request_id,
            "training_type": training_type,
            "status": status
        }
        
    except Exception as e:
        logger.exception(f"Ошибка проверки статуса обучения: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 1.5 Обновление .env.example для отладки

**Создать/дополнить**: `.env.example`

```bash
# ==================== FAL AI TRAINING SETTINGS ====================

# API ключ для FAL AI
FAL_API_KEY=your_fal_api_key_here

# 🧪 РЕЖИМ ОТЛАДКИ - НЕ ЗАПУСКАЕТ РЕАЛЬНОЕ ОБУЧЕНИЕ
# Установите False только в продакшне!
FAL_TRAINING_TEST_MODE=true

# Webhook для уведомлений о статусе обучения
FAL_WEBHOOK_URL=https://yourdomain.com/api/avatar/status_update

# Настройки тестового режима
FAL_MOCK_TRAINING_DURATION=30
FAL_ENABLE_WEBHOOK_SIMULATION=true

# Основные настройки
FAL_DEFAULT_MODE=character
FAL_DEFAULT_ITERATIONS=500
FAL_DEFAULT_PRIORITY=quality

# Портретный тренер
FAL_PORTRAIT_STEPS=1000
FAL_PORTRAIT_LEARNING_RATE=0.0002
FAL_PORTRAIT_SUBJECT_CROP=true
FAL_PORTRAIT_CREATE_MASKS=true

# Расширенные настройки
FAL_TRAINING_TIMEOUT=1800
FAL_STATUS_CHECK_INTERVAL=30
FAL_AUTO_MODEL_SELECTION=true
``` 