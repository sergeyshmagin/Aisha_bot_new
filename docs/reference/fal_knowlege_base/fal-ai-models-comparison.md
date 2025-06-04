# Сравнение моделей FAL AI для обучения аватаров

## 📋 Обзор доступных моделей

### 1. `fal-ai/flux-pro-trainer`
- **Тип**: Полное обучение + LoRA
- **Специализация**: Универсальная модель
- **Качество**: ⭐⭐⭐⭐⭐ (Очень высокое)
- **Скорость**: ⭐⭐⭐ (Средняя)
- **Гибкость**: ⭐⭐⭐⭐⭐ (Максимальная)

### 2. `fal-ai/flux-lora-portrait-trainer`
- **Тип**: LoRA специально для портретов
- **Специализация**: Портреты
- **Качество**: ⭐⭐⭐⭐⭐ (Очень высокое для портретов)
- **Скорость**: ⭐⭐⭐⭐ (Быстрая)
- **Гибкость**: ⭐⭐⭐ (Ограниченная портретами)

## 🎯 Рекомендации по выбору

### Для портретов людей → `flux-lora-portrait-trainer`
```python
# Оптимальные настройки для портретов
{
    "images_data_url": "training_data.zip",
    "trigger_phrase": "TOK_person",
    "steps": 1000,
    "learning_rate": 0.0002,
    "subject_crop": True,
    "create_masks": True,
    "multiresolution_training": True
}
```

**Преимущества**:
- ✅ Специально оптимизирован для лиц
- ✅ Автоматическая обрезка субъекта
- ✅ Создание масок для лучшего качества
- ✅ Быстрое обучение (1000-2500 шагов)
- ✅ Отличное качество портретов

**Когда использовать**:
- Аватары людей
- Персональные портреты
- Селфи-стили
- Профессиональные фото

### Для стилей и объектов → `flux-pro-trainer`
```python
# Оптимальные настройки для стилей
{
    "data_url": "training_data.zip", 
    "mode": "style",
    "finetune_type": "lora",
    "iterations": 500,
    "learning_rate": 1e-4,
    "trigger_word": "TOK_style",
    "lora_rank": 32,
    "priority": "quality"
}
```

**Преимущества**:
- ✅ Поддержка разных режимов (character, style, product, general)
- ✅ Полное обучение и LoRA
- ✅ Гибкая настройка параметров
- ✅ Автоматическое создание подписей
- ✅ Разные приоритеты (speed/quality/high_res_only)

**Когда использовать**:
- Художественные стили
- Продукты и объекты
- Архитектура и интерьеры
- Абстрактные концепции

## 📊 Детальное сравнение

| Параметр | flux-pro-trainer | flux-lora-portrait-trainer |
|----------|------------------|---------------------------|
| **Основное назначение** | Универсальное обучение | Портреты людей |
| **Типы моделей** | Full + LoRA | Только LoRA |
| **Время обучения** | 5-30 минут | 3-15 минут |
| **Количество шагов** | 300-1000+ | 1000-2500 |
| **Learning rate** | 1e-5 (full), 1e-4 (LoRA) | 0.00009-0.0002 |
| **Автообрезка** | ❌ | ✅ |
| **Создание масок** | ❌ | ✅ |
| **Мультиразрешение** | ❌ | ✅ |
| **Автоподписи** | ✅ | ❌ |
| **Режимы обучения** | character, style, product, general | portrait (фиксированный) |

## 🛠️ Интеграция в проект

### Класс-адаптер для выбора модели

```python
from enum import Enum
from typing import Dict, Any, Optional
import fal_client

class FALModelType(str, Enum):
    PORTRAIT = "portrait"
    STYLE = "style"
    PRODUCT = "product"
    GENERAL = "general"

class FALTrainerAdapter:
    """Адаптер для выбора оптимальной FAL AI модели"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            import os
            os.environ['FAL_KEY'] = api_key
    
    async def train_avatar(
        self,
        model_type: FALModelType,
        images_data_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Обучает аватар, автоматически выбирая оптимальную модель
        
        Args:
            model_type: Тип модели для обучения
            images_data_url: URL к данным для обучения
            **kwargs: Дополнительные параметры
        """
        if model_type == FALModelType.PORTRAIT:
            return await self._train_portrait(images_data_url, **kwargs)
        else:
            return await self._train_general(model_type, images_data_url, **kwargs)
    
    async def _train_portrait(
        self,
        images_data_url: str,
        trigger_phrase: Optional[str] = None,
        steps: int = 1000,
        learning_rate: float = 0.0002,
        **kwargs
    ) -> Dict[str, Any]:
        """Обучение портретной модели"""
        
        arguments = {
            "images_data_url": images_data_url,
            "steps": steps,
            "learning_rate": learning_rate,
            "subject_crop": True,
            "create_masks": True,
            "multiresolution_training": True,
            **kwargs
        }
        
        if trigger_phrase:
            arguments["trigger_phrase"] = trigger_phrase
        
        return fal_client.subscribe(
            "fal-ai/flux-lora-portrait-trainer",
            arguments=arguments,
            with_logs=True
        )
    
    async def _train_general(
        self,
        model_type: FALModelType,
        data_url: str,
        iterations: int = 500,
        learning_rate: float = 1e-4,
        trigger_word: str = "TOK",
        **kwargs
    ) -> Dict[str, Any]:
        """Обучение универсальной модели"""
        
        # Маппинг типов на режимы flux-pro-trainer
        mode_mapping = {
            FALModelType.STYLE: "style",
            FALModelType.PRODUCT: "product", 
            FALModelType.GENERAL: "general"
        }
        
        arguments = {
            "data_url": data_url,
            "mode": mode_mapping[model_type],
            "finetune_type": "lora",
            "iterations": iterations,
            "learning_rate": learning_rate,
            "trigger_word": trigger_word,
            "lora_rank": 32,
            "priority": "quality",
            "captioning": True,
            **kwargs
        }
        
        return fal_client.subscribe(
            "fal-ai/flux-pro-trainer",
            arguments=arguments,
            with_logs=True
        )
    
    def get_optimal_settings(self, model_type: FALModelType) -> Dict[str, Any]:
        """Возвращает оптимальные настройки для типа модели"""
        
        if model_type == FALModelType.PORTRAIT:
            return {
                "steps": 1000,
                "learning_rate": 0.0002,
                "subject_crop": True,
                "create_masks": True,
                "multiresolution_training": True
            }
        else:
            return {
                "iterations": 500,
                "learning_rate": 1e-4,
                "finetune_type": "lora",
                "lora_rank": 32,
                "priority": "quality",
                "captioning": True
            }
```

### Использование в сервисе аватаров

```python
# В app/services/avatar/training_service.py

from .fal_trainer_adapter import FALTrainerAdapter, FALModelType

class AvatarTrainingService:
    def __init__(self):
        self.fal_adapter = FALTrainerAdapter()
    
    async def start_training(
        self, 
        avatar_id: UUID, 
        avatar_type: str,
        training_data_url: str
    ) -> str:
        """Запускает обучение аватара с автовыбором модели"""
        
        # Определяем тип модели на основе типа аватара
        if avatar_type == "character":
            model_type = FALModelType.PORTRAIT
            trigger_phrase = f"TOK_{avatar_id.hex[:8]}"
            
            result = await self.fal_adapter.train_avatar(
                model_type=model_type,
                images_data_url=training_data_url,
                trigger_phrase=trigger_phrase
            )
            
        else:  # style, product, etc.
            model_type_mapping = {
                "style": FALModelType.STYLE,
                "product": FALModelType.PRODUCT
            }
            model_type = model_type_mapping.get(avatar_type, FALModelType.GENERAL)
            trigger_word = f"TOK_{avatar_id.hex[:8]}"
            
            result = await self.fal_adapter.train_avatar(
                model_type=model_type,
                images_data_url=training_data_url,
                trigger_word=trigger_word
            )
        
        return result.get("finetune_id") or result.get("request_id")
```

## 📈 Оптимизация параметров

### Для быстрого прототипирования

```python
# Portrait (быстрое обучение)
{
    "steps": 500,
    "learning_rate": 0.0003,
    "subject_crop": True
}

# General (быстрое обучение)
{
    "iterations": 200,
    "learning_rate": 2e-4,
    "priority": "speed"
}
```

### Для максимального качества

```python
# Portrait (высокое качество)
{
    "steps": 2500,
    "learning_rate": 0.0001,
    "subject_crop": True,
    "create_masks": True,
    "multiresolution_training": True
}

# General (высокое качество)
{
    "iterations": 1000,
    "learning_rate": 5e-5,
    "priority": "quality",
    "lora_rank": 32
}
```

### Для продукции

```python
# Portrait (продакшн)
{
    "steps": 1500,
    "learning_rate": 0.00015,
    "subject_crop": True,
    "create_masks": True
}

# General (продакшн)
{
    "iterations": 600,
    "learning_rate": 8e-5,
    "priority": "quality",
    "lora_rank": 32
}
```

## 🚨 Обработка ошибок

```python
async def safe_train_avatar(self, model_type: FALModelType, **kwargs):
    """Безопасное обучение с обработкой ошибок"""
    try:
        result = await self.train_avatar(model_type, **kwargs)
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "insufficient data" in error_msg:
            raise ValueError("Недостаточно данных для обучения (минимум 10 изображений)")
        elif "invalid format" in error_msg:
            raise ValueError("Неверный формат данных (требуется ZIP архив)")
        elif "rate limit" in error_msg:
            raise ValueError("Превышен лимит запросов, попробуйте позже")
        elif "quota exceeded" in error_msg:
            raise ValueError("Превышена квота API")
        else:
            raise ValueError(f"Ошибка обучения: {e}")
```

## 💰 Рекомендации по стоимости

1. **Portrait Trainer**: Оптимален для массового создания аватаров людей
2. **Pro Trainer (LoRA)**: Баланс стоимости и качества для разных типов
3. **Pro Trainer (Full)**: Максимальное качество для премиум аватаров

## 🔗 Дополнительные ресурсы

- [FAL AI Flux Pro Trainer](https://fal.ai/models/fal-ai/flux-pro-trainer)
- [FAL AI Portrait Trainer](https://fal.ai/models/fal-ai/flux-lora-portrait-trainer)
- [FAL AI Python Client](https://github.com/fal-ai/fal)
- [Документация по обучению](https://fal.ai/docs/training) 