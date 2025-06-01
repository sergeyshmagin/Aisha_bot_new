# 🛠️ Устранение проблем с аватарами

**Дата создания**: 2025-05-31  
**Дата обновления**: 2025-05-31  
**Статус**: АКТИВНО

## 🚨 Частые проблемы и решения

### 1. Ошибка "finetune ID does not exist yet"

**Симптомы**:
- Генерация изображений падает с ошибкой `422 Unprocessable Entity`
- В логах: "The finetune ID you provided does not exist yet"
- Система правильно определяет тип аватара как STYLE

**Причины**:
- FAL AI удалил старые finetune модели (>30 дней)
- Изменения в политике хранения FAL AI
- Ошибка при сохранении результатов обучения
- Некорректный формат finetune_id (не UUID)

**🔧 Быстрое решение через FinetuneUpdaterService**:

```python
# 1. Обновление конкретного аватара по имени
from app.services.avatar.finetune_updater_service import FinetuneUpdaterService
from app.core.database import get_session

async with get_session() as session:
    updater = FinetuneUpdaterService(session)
    
    success = await updater.update_finetune_id_by_name(
        avatar_name="SERGEY-STYLE-PROD",
        new_finetune_id="5ae6bfaa-3970-47c5-afd2-085c67a8ef07",
        reason="Updated to valid finetune_id from FAL AI",
        updated_by="admin_manual_update"
    )
```

**🔍 Автоматическая проверка через Status Checker**:

```python
from app.services.avatar.fal_training_service.status_checker import status_checker

# Проверка всех аватаров с некорректными finetune_id
result = await status_checker.check_and_fix_invalid_finetune_ids()

# Обновление конкретного аватара
success = await status_checker.update_finetune_id_if_needed(
    avatar_id=UUID("8fe7790b-9a0d-4def-9dd1-c776784cf6b1"),
    new_finetune_id="5ae6bfaa-3970-47c5-afd2-085c67a8ef07",
    reason="Production finetune_id update"
)
```

**📊 Массовое обновление при миграции**:

```python
# Маппинг старых ID на новые (получить от FAL AI)
mapping = {
    "sergey-style-prod": "5ae6bfaa-3970-47c5-afd2-085c67a8ef07",
    "anna-style-prod": "b2c3d4e5-1234-5678-9abc-def012345678",
    "mike-style-dev": "c3d4e5f6-2345-6789-abcd-ef0123456789"
}

result = await updater.bulk_update_invalid_finetune_ids(
    finetune_id_mapping=mapping,
    reason="Migration to new FAL AI finetune IDs",
    updated_by="fal_migration_script"
)
```

### 2. Нарушение правил валидации

**Симптомы**:
- Style аватар имеет LoRA файл вместо finetune_id
- Portrait аватар имеет finetune_id вместо LoRA файла
- Смешанные данные в аватаре

**Автоматическое исправление через Валидатор**:
```python
from app.services.avatar.training_data_validator import AvatarTrainingDataValidator

async with get_session() as session:
    validator = AvatarTrainingDataValidator(session)
    
    # Валидация перед обучением
    is_ready, message = await validator.validate_avatar_before_training(avatar)
    
    # Исправление данных завершения
    update_data = await validator.validate_and_fix_training_completion(
        avatar=avatar,
        webhook_result=webhook_result
    )
```

### 3. Поиск аватаров с проблемами

**🔍 Диагностические скрипты**:

```bash
# Тестирование FinetuneUpdaterService
python test_finetune_updater.py

# Проверка конкретного аватара  
python update_sergey_finetune_id.py

# Тестирование валидатора
python test_validator.py
```

**🔍 Программная диагностика**:

```python
# Поиск аватаров с некорректными finetune_id
invalid_avatars = await updater.find_avatars_with_invalid_finetune_ids()

# Получение истории обновлений
history = await updater.get_update_history(avatar_id)
```

### 4. Устаревшие данные обучения

**Симптомы**:
- Аватар создан >30 дней назад
- FAL AI API возвращает 404 для finetune_id
- Генерация не работает

**Решение**:
1. Получить новый finetune_id от FAL AI
2. Обновить через FinetuneUpdaterService
3. Проверить готовность к генерации

### 5. Некорректный формат finetune_id

**Симптомы**:
- finetune_id не в формате UUID
- Примеры некорректных: `sergey-style-prod`, `model-123`, `test-finetune`

**Валидация формата**:
```python
# Проверка формата UUID
is_valid = updater._is_valid_uuid("5ae6bfaa-3970-47c5-afd2-085c67a8ef07")  # True
is_valid = updater._is_valid_uuid("sergey-style-prod")  # False
```

## 🛠️ Новые сервисы и инструменты

### FinetuneUpdaterService

**Функции**:
- ✅ Обновление finetune_id по имени или ID аватара
- ✅ Валидация формата UUID
- ✅ Массовое обновление с маппингом
- ✅ Поиск проблемных аватаров
- ✅ История обновлений с аудитом
- ✅ Соблюдение правил валидации (Style/Portrait)

**Интеграция с Status Checker**:
- ✅ Автоматическая проверка при мониторинге
- ✅ Обновление через единый API
- ✅ Логирование и отчетность

### Улучшенный валидатор данных

**Улучшения**:
- ✅ Строгая валидация UUID формата для finetune_id
- ✅ Приоритетная проверка полей в правильном порядке
- ✅ Подробное логирование процесса извлечения
- ✅ Отклонение неправильных форматов
- ✅ Поддержка UUID с дефисами и без

## 📚 Примеры использования

### Обновление SERGEY-STYLE-PROD

```python
# Пример успешного обновления
avatar_name = "SERGEY-STYLE-PROD"
new_finetune_id = "5ae6bfaa-3970-47c5-afd2-085c67a8ef07"

async with get_session() as session:
    updater = FinetuneUpdaterService(session)
    
    success = await updater.update_finetune_id_by_name(
        avatar_name=avatar_name,
        new_finetune_id=new_finetune_id,
        reason="Updated to valid FAL AI finetune_id",
        updated_by="admin_update"
    )
    
    if success:
        print("✅ Аватар обновлен и готов к генерации")
```

### Проверка готовности к генерации

```python
# Проверка всех критериев
def check_generation_readiness(avatar):
    return (
        avatar.status == AvatarStatus.COMPLETED and
        avatar.training_type == AvatarTrainingType.STYLE and
        avatar.finetune_id and
        not avatar.diffusers_lora_file_url and
        avatar.trigger_word
    )
```

## 🚨 Критические правила

1. **Style аватары**: ТОЛЬКО `finetune_id` (UUID формат) + `trigger_word`
2. **Portrait аватары**: ТОЛЬКО `diffusers_lora_file_url` + `trigger_phrase`
3. **finetune_id формат**: Строго UUID, например `5ae6bfaa-3970-47c5-afd2-085c67a8ef07`
4. **Аудит изменений**: Все обновления логируются в `avatar_data.finetune_update_history`
5. **Валидация**: Используйте только `AvatarTrainingDataValidator` и `FinetuneUpdaterService`

## 📞 Поддержка

При возникновении проблем:
1. Запустите диагностические скрипты
2. Проверьте логи `app.services.avatar`
3. Используйте FinetuneUpdaterService для исправления
4. Обратитесь к документации FAL AI для получения новых finetune_id

## 🔧 Диагностические скрипты

### `check_avatar_data.py`
Проверяет конкретный аватар:
```bash
python check_avatar_data.py
```

### `check_all_avatars.py`
Проверяет все завершенные аватары:
```bash
python check_all_avatars.py
```

### `fix_all_avatar_issues.py`
Исправляет все найденные проблемы:
```bash
python fix_all_avatar_issues.py
```

## 📋 Правила валидации (напоминание)

### Style аватары:
- ✅ **ДОЛЖНЫ иметь**: `finetune_id`, `trigger_word`
- ❌ **НЕ должны иметь**: `diffusers_lora_file_url`
- 🎯 **API**: `fal-ai/flux-pro/v1.1-ultra-finetuned`

### Portrait аватары:
- ✅ **ДОЛЖНЫ иметь**: `diffusers_lora_file_url`, `trigger_phrase`
- ❌ **НЕ должны иметь**: `finetune_id`
- 🎯 **API**: `fal-ai/flux-lora`

## 🔄 Процедура восстановления

### При недействительном finetune_id:

1. **Идентификация проблемы**:
   ```
   ERROR: The finetune ID you provided does not exist yet
   ```

2. **Проверка аватара**:
   ```bash
   python check_avatar_data.py
   ```

3. **Варианты исправления**:
   - **Переобучение**: Статус → `READY_FOR_TRAINING`
   - **Ошибка**: Статус → `ERROR`
   - **Очистка**: Убрать данные обучения

4. **Автоматическое исправление**:
   ```bash
   python fix_all_avatar_issues.py
   ```

### При нарушении структуры:

1. **Система валидации автоматически**:
   - Удаляет конфликтующие поля
   - Устанавливает правильные триггеры
   - Записывает историю исправлений

2. **Проверка результата**:
   ```bash
   python check_avatar_data.py
   ```

## 📈 Мониторинг

### Регулярные проверки:
```bash
# Еженедельно проверяем все аватары
python check_all_avatars.py

# При обнаружении проблем
python fix_all_avatar_issues.py
```

### Логирование исправлений:
Все исправления записываются в `avatar_data.fix_history`:
```json
{
  "timestamp": "2025-05-31T22:00:00Z",
  "reason": "Invalid finetune_id: sergey-style-prod",
  "action": "reset_for_retraining",
  "old_finetune_id": "sergey-style-prod"
}
```

## 🚨 Экстренные меры

### Если система генерации полностью не работает:

1. **Быстрая диагностика**:
   ```bash
   python check_all_avatars.py | grep "❌"
   ```

2. **Массовое исправление**:
   ```bash
   python fix_all_avatar_issues.py
   ```

3. **Перезапуск системы валидации**:
   ```python
   from app.services.avatar.training_data_validator import AvatarTrainingDataValidator
   # Валидатор будет применен автоматически
   ```

---

**ВАЖНО**: При любых изменениях в аватарах всегда создается история исправлений для отслеживания изменений! 