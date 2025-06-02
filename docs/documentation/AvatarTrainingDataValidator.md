# Avatar Training Data Validator - Документация

**Файл:** `app/services/avatar/training_data_validator.py`  
**Класс:** `AvatarTrainingDataValidator`  
**Назначение:** Валидация и исправление данных при обучении аватаров

## Описание

`AvatarTrainingDataValidator` обеспечивает строгое соблюдение правил хранения данных обучения аватаров. Класс гарантирует, что портретные аватары используют только LoRA файлы, а также валидирует корректность данных перед сохранением.

## Строгие правила

- **Portrait аватары**: ТОЛЬКО `diffusers_lora_file_url`, `finetune_id = NULL`
- **Валидация данных**: Проверка корректности webhook результатов
- **Очистка конфликтов**: Автоматическое исправление несовместимых данных

## Основные методы

### `__init__(self, session: AsyncSession)`
Инициализирует валидатор с сессией базы данных.

**Параметры:**
- `session` (AsyncSession): Асинхронная сессия SQLAlchemy

### `async def validate_and_fix_training_completion(avatar, webhook_result)`
Основной метод валидации и исправления данных завершения обучения.

**Параметры:**
- `avatar` (Avatar): Модель аватара для обновления
- `webhook_result` (Dict[str, Any]): Результат от FAL AI webhook

**Возвращает:**
- `Dict[str, Any]`: Исправленные данные для обновления аватара

**Процесс валидации:**
1. Установка базовых данных (статус, прогресс, время завершения)
2. Обеспечение trigger фразы/слова
3. Применение строгих правил по типам аватаров
4. Финальная валидация данных

**Пример:**
```python
validator = AvatarTrainingDataValidator(session)
update_data = await validator.validate_and_fix_training_completion(
    avatar=avatar,
    webhook_result=webhook_data
)
```

### `def _extract_lora_url(self, webhook_result)`
Извлекает URL LoRA файла из результата webhook.

**Поддерживаемые структуры:**
- Прямой URL: `result.diffusers_lora_file_url`
- Объект с URL: `result.diffusers_lora_file.url`
- Массив файлов: `result.files[].url` (где type="lora")

### `def _extract_config_url(self, webhook_result)`
Извлекает URL конфигурационного файла.

**Поддерживаемые структуры:**
- Прямой URL: `result.config_file_url`
- Объект с URL: `result.config_file.url`
- Массив файлов: `result.files[].url` (где type="config")

### `async def validate_avatar_before_training(avatar)`
Валидирует аватар перед запуском обучения.

**Проверки:**
- Статус аватара (должен быть PENDING)
- Наличие типа обучения
- Поддержка типа обучения (только PORTRAIT)
- Полнота обязательных данных
- Отсутствие конфликтующих данных

**Возвращает:**
- `Tuple[bool, str]`: (готов_к_обучению, сообщение)

**Пример:**
```python
is_ready, message = await validator.validate_avatar_before_training(avatar)
if not is_ready:
    raise ValueError(f"Аватар не готов к обучению: {message}")
```

## Конфигурация обучения

### `def get_training_config_for_type(training_type, user_preferences)`
Возвращает правильную конфигурацию для типа аватара.

**Для Portrait аватаров:**
```python
{
    "training_type": "portrait",
    "trigger_type": "phrase",
    "api_endpoint": "flux-lora-portrait-trainer",
    "expected_result": "diffusers_lora_file",
    "quality": "balanced"  # или из user_preferences
}
```

## Обработка ошибок

### Критические ошибки
При отсутствии ожидаемых данных валидатор устанавливает fallback значения:

**Portrait аватары без LoRA:**
```python
fallback_lora = f"https://fallback-lora.com/{avatar.name.lower()}-{avatar.id.hex[:8]}.safetensors"
fallback_config = f"https://fallback-lora.com/{avatar.name.lower()}-{avatar.id.hex[:8]}-config.json"
```

### Очистка конфликтующих данных
```python
async def _clear_training_data(self, avatar_id: UUID) -> None:
    """Очищает старые данные обучения"""
    stmt = update(Avatar).where(Avatar.id == avatar_id).values(
        finetune_id=None,
        diffusers_lora_file_url=None,
        config_file_url=None,
        fal_response_data=None
    )
```

## Парсинг временных меток

### `def _parse_completed_at(completed_at_str)`
Парсит строку времени завершения в datetime объект.

**Поддерживаемые форматы:**
- ISO формат: `2025-05-23T16:30:00Z`
- Без микросекунд: `2025-05-23T16:30:00`
- Fallback: `datetime.utcnow()` при ошибке парсинга

## Примеры использования

### Полный цикл валидации:
```python
# 1. Создание валидатора
validator = AvatarTrainingDataValidator(session)

# 2. Проверка готовности к обучению
is_ready, message = await validator.validate_avatar_before_training(avatar)
if not is_ready:
    logger.error(f"Аватар не готов: {message}")
    return

# 3. Получение конфигурации
config = validator.get_training_config_for_type(
    training_type=avatar.training_type,
    user_preferences={"quality": "high"}
)

# 4. После получения webhook
update_data = await validator.validate_and_fix_training_completion(
    avatar=avatar,
    webhook_result=webhook_data
)

# 5. Обновление аватара
stmt = update(Avatar).where(Avatar.id == avatar.id).values(**update_data)
await session.execute(stmt)
await session.commit()
```

### Обработка ошибок валидации:
```python
try:
    update_data = await validator.validate_and_fix_training_completion(
        avatar, webhook_result
    )
except ValueError as e:
    logger.error(f"Ошибка валидации: {e}")
    # Установить статус ошибки
    avatar.status = AvatarStatus.ERROR
    await session.commit()
```

## Логирование

Все операции логируются с детальной информацией:
- **INFO**: Успешная валидация и исправления
- **WARNING**: Fallback значения и очистка данных
- **ERROR**: Критические ошибки валидации
- **DEBUG**: Детали извлечения данных из webhook

## Интеграция

### С AvatarTrainingService
```python
# В процессе завершения обучения
validator = AvatarTrainingDataValidator(self.session)
update_data = await validator.validate_and_fix_training_completion(
    avatar, webhook_result
)
```

### С FAL Webhook Handler
```python
# При получении webhook
async def handle_training_completion(webhook_data):
    validator = AvatarTrainingDataValidator(session)
    update_data = await validator.validate_and_fix_training_completion(
        avatar, webhook_data
    )
    # Применение обновлений...
```

## Лучшие практики

1. **Всегда валидировать перед обучением:**
   ```python
   is_ready, message = await validator.validate_avatar_before_training(avatar)
   assert is_ready, f"Валидация не пройдена: {message}"
   ```

2. **Использовать транзакции:**
   ```python
   async with session.begin():
       update_data = await validator.validate_and_fix_training_completion(...)
       await session.execute(update_stmt)
   ```

3. **Логировать все изменения:**
   ```python
   logger.info(f"Валидация завершена для аватара {avatar.id}: {update_data}")
   ```

## См. также

- [Avatar Training Service](./AvatarTrainingService.md)
- [FAL AI Client](./FALAIClient.md)
- [Avatar Photo Service](./AvatarPhotoService.md) 