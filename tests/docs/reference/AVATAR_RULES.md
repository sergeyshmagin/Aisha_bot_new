# 📋 Строгие правила для типов аватаров

**Дата создания**: 2025-05-31  
**Статус**: ОБЯЗАТЕЛЬНО К СОБЛЮДЕНИЮ

## 🎯 Основные правила

### 🎨 Style аватары (Художественные стили)
- **Тип обучения**: `AvatarTrainingType.STYLE`
- **Данные**: ОБЯЗАТЕЛЬНО `finetune_id` 
- **API**: `fal-ai/flux-pro/v1.1-ultra-finetuned`
- **Триггер**: `trigger_word`
- **Запрещено**: `diffusers_lora_file_url` должно быть `NULL`

### 👤 Portrait аватары (Портретные)
- **Тип обучения**: `AvatarTrainingType.PORTRAIT`
- **Данные**: ОБЯЗАТЕЛЬНО `diffusers_lora_file_url`
- **API**: `fal-ai/flux-lora`
- **Триггер**: `trigger_phrase` (или `trigger_word` как fallback)
- **Запрещено**: `finetune_id` должно быть `NULL`

## ❌ Типичные ошибки и их исправление

### Ошибка 1: Style аватар с LoRA файлом
```
❌ НЕПРАВИЛЬНО:
training_type: STYLE
finetune_id: NULL
diffusers_lora_file_url: "https://url.com/lora/file.safetensors"

✅ ПРАВИЛЬНО:
training_type: STYLE  
finetune_id: "sergey-style-prod"
diffusers_lora_file_url: NULL
```

### Ошибка 2: Portrait аватар с finetune_id
```
❌ НЕПРАВИЛЬНО:
training_type: PORTRAIT
finetune_id: "some-finetune-id"
diffusers_lora_file_url: NULL

✅ ПРАВИЛЬНО:
training_type: PORTRAIT
finetune_id: NULL
diffusers_lora_file_url: "https://url.com/lora/file.safetensors"
```

## 🔧 Автоматические проверки

Система выполняет следующие проверки при генерации:

1. **Проверка соответствия типа и данных**
2. **Проверка отсутствия конфликтующих данных**
3. **Выбор правильного API на основе типа**
4. **Логирование ошибок с четким описанием проблемы**

## 🚀 API Endpoints

### Style аватары → FLUX1.1 [pro] ultra Fine-tuned
```python
endpoint = "fal-ai/flux-pro/v1.1-ultra-finetuned"
arguments = {
    "finetune_id": avatar.finetune_id,
    "finetune_strength": 1.1,
    "aspect_ratio": "1:1"
}
```

### Portrait аватары → flux-lora
```python
endpoint = "fal-ai/flux-lora"  
arguments = {
    "lora_url": avatar.diffusers_lora_file_url,
    "lora_scale": 1.0,
    "image_size": "square_hd"
}
```

## 📊 Диагностика проблем

При возникновении ошибок в логах ищите:

- `❌ ОШИБКА ДАННЫХ:` - неправильное соответствие типа и данных
- `⚠️` - предупреждения о конфликтующих данных
- `✅` - успешная проверка аватара

## 🔄 Исправление данных

Если обнаружена ошибка в данных аватара:

1. **Определите правильный тип** на основе назначения аватара
2. **Переместите данные** в правильное поле
3. **Очистите неправильное поле**
4. **Обновите тип** если необходимо

Пример исправления:
```sql
-- Для стилевого аватара
UPDATE avatars SET 
    training_type = 'STYLE',
    finetune_id = 'extracted-from-url',
    diffusers_lora_file_url = NULL
WHERE name LIKE '%STYLE%';
```

## ⚡ Производительность

- **Style аватары**: Быстрее на 10x благодаря ultra API
- **Portrait аватары**: Стабильная генерация через проверенный LoRA API
- **Разделение**: Избегает конфликтов и неопределенности

---

**ВАЖНО**: Эти правила ОБЯЗАТЕЛЬНЫ для корректной работы системы генерации! 