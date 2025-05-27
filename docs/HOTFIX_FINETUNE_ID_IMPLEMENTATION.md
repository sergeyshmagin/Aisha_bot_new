# Hotfix: Исправление реализации Fine-tune ID

## 🎯 Проблема
В текущей реализации есть путаница между `request_id` и `finetune_id`, а также неправильная обработка результатов разных моделей FAL AI.

## 🔍 Анализ проблем

### ❌ 1. Путаница между request_id и finetune_id
**Текущий код смешивает два разных ID:**
- **`request_id`** - возвращается сразу при отправке задачи
- **`finetune_id`** - возвращается в результате после завершения обучения

### ❌ 2. Неправильное получение finetune_id
```python
# НЕПРАВИЛЬНО - блокирующий вызов
result = await handler.get()
finetune_id = result.get("finetune_id")
```

### ❌ 3. Разные модели возвращают разные результаты
- **flux-pro-trainer**: возвращает `finetune_id`
- **flux-lora-portrait-trainer**: возвращает файлы LoRA, НЕ `finetune_id`

## ✅ Правильная реализация

### 1. Исправление FAL клиента

**БЫЛО:**
```python
async def _submit_training(self, data_url: str, user_id: UUID, avatar_id: UUID, config: Dict[str, Any]) -> Optional[str]:
    handler = await fal_client.submit_async(
        "fal-ai/flux-pro-trainer",
        arguments=arguments,
        webhook_url=config.get("webhook_url")
    )
    
    # НЕПРАВИЛЬНО - блокирующий вызов
    result = await handler.get()
    finetune_id = result.get("finetune_id")
    return finetune_id
```

**СТАЛО:**
```python
async def _submit_training(self, data_url: str, user_id: UUID, avatar_id: UUID, config: Dict[str, Any]) -> Optional[str]:
    handler = await fal_client.submit_async(
        "fal-ai/flux-pro-trainer",
        arguments=arguments,
        webhook_url=config.get("webhook_url")
    )
    
    # ПРАВИЛЬНО - возвращаем request_id сразу
    request_id = handler.request_id
    return request_id  # finetune_id придет позже в webhook
```

### 2. Обновление модели Avatar

**Добавляем поля для правильного хранения:**
```python
class Avatar(Base):
    # Отслеживание обучения
    fal_request_id: str = mapped_column(String(255), nullable=True, index=True)  # Для отслеживания
    finetune_id: str = mapped_column(String(255), nullable=True, index=True)     # Для генерации
    
    # Результаты обучения (для разных типов моделей)
    diffusers_lora_file_url: str = mapped_column(String(500), nullable=True)     # LoRA файл
    config_file_url: str = mapped_column(String(500), nullable=True)             # Конфиг
    fal_response_data: Dict = mapped_column(JSON, default=dict)                  # Полный ответ
```

### 3. Исправление обработки webhook

**БЫЛО:**
```python
async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
    finetune_id = webhook_data.get("finetune_id")
    # Ищем по finetune_id (которого может не быть)
    avatar_id = await self._find_avatar_by_finetune_id(finetune_id)
```

**СТАЛО:**
```python
async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
    # Ищем по request_id (который всегда есть)
    request_id = webhook_data.get("request_id")
    avatar = await self._find_avatar_by_request_id(request_id)
    
    if not avatar:
        return False
    
    # Обрабатываем результат в зависимости от типа модели
    await self._process_training_result(avatar, webhook_data)
```

### 4. Обработка результатов разных моделей

```python
async def _process_training_result(self, avatar: Avatar, webhook_data: Dict[str, Any]) -> None:
    status = webhook_data.get("status")
    
    if status == "completed":
        result = webhook_data.get("result", {})
        
        if avatar.training_type == AvatarTrainingType.PORTRAIT:
            # flux-lora-portrait-trainer - сохраняем файлы LoRA
            diffusers_file = result.get("diffusers_lora_file", {})
            config_file = result.get("config_file", {})
            
            update_data = {
                "status": AvatarStatus.COMPLETED,
                "diffusers_lora_file_url": diffusers_file.get("url"),
                "config_file_url": config_file.get("url"),
                "fal_response_data": result,
                "training_completed_at": datetime.utcnow()
            }
            
        else:
            # flux-pro-trainer - сохраняем finetune_id
            finetune_id = result.get("finetune_id")
            
            update_data = {
                "status": AvatarStatus.COMPLETED,
                "finetune_id": finetune_id,
                "fal_response_data": result,
                "training_completed_at": datetime.utcnow()
            }
        
        # Обновляем аватар
        await self._update_avatar(avatar.id, update_data)
```

### 5. Генерация изображений

```python
async def generate_image(self, avatar_id: UUID, prompt: str) -> Optional[str]:
    avatar = await self._get_avatar(avatar_id)
    
    if avatar.training_type == AvatarTrainingType.PORTRAIT:
        # Для портретных аватаров используем LoRA файл
        if not avatar.diffusers_lora_file_url:
            raise ValueError("LoRA файл не найден")
        
        # Генерация с LoRA адаптером
        result = await fal_client.submit_async(
            "fal-ai/flux-lora",
            arguments={
                "prompt": prompt,
                "lora_url": avatar.diffusers_lora_file_url,
                "trigger_phrase": avatar.trigger_phrase
            }
        )
        
    else:
        # Для стилевых аватаров используем finetune_id
        if not avatar.finetune_id:
            raise ValueError("Finetune ID не найден")
        
        # Генерация с fine-tuned моделью
        result = await fal_client.submit_async(
            "fal-ai/flux-pro",
            arguments={
                "prompt": prompt,
                "model": avatar.finetune_id,
                "trigger_word": avatar.trigger_word
            }
        )
    
    return result.get("images", [{}])[0].get("url")
```

## 🔄 Миграция базы данных

```python
# Новая миграция для исправления полей
def upgrade():
    # Добавляем новые поля если их нет
    op.add_column('avatars', sa.Column('diffusers_lora_file_url', sa.String(500), nullable=True))
    op.add_column('avatars', sa.Column('config_file_url', sa.String(500), nullable=True))
    
    # Создаем индексы
    op.create_index('ix_avatars_fal_request_id', 'avatars', ['fal_request_id'])
    op.create_index('ix_avatars_finetune_id', 'avatars', ['finetune_id'])
```

## 🧪 Тестирование

### Тест 1: Портретное обучение
1. ✅ Запустить обучение портретного аватара
2. ✅ Проверить что сохраняется `fal_request_id`
3. ✅ Дождаться webhook с результатом
4. ✅ Проверить что сохраняются `diffusers_lora_file_url` и `config_file_url`
5. ✅ Проверить генерацию с LoRA адаптером

### Тест 2: Стилевое обучение
1. ✅ Запустить обучение стилевого аватара
2. ✅ Проверить что сохраняется `fal_request_id`
3. ✅ Дождаться webhook с результатом
4. ✅ Проверить что сохраняется `finetune_id`
5. ✅ Проверить генерацию с fine-tuned моделью

## 📊 Результат

### ✅ Правильная архитектура:
- **request_id** - для отслеживания процесса обучения
- **finetune_id** - для генерации (только для flux-pro-trainer)
- **diffusers_lora_file_url** - для генерации (только для flux-lora-portrait-trainer)

### ✅ Универсальность:
- Поддержка разных типов моделей FAL AI
- Правильная обработка результатов каждой модели
- Корректная генерация изображений для каждого типа

### ✅ Надежность:
- Нет блокирующих вызовов при запуске обучения
- Правильная обработка webhook
- Безопасное сохранение результатов 