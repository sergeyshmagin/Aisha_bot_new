# 🚨 Исправление проблем обучения аватаров

## 📊 Обнаруженные проблемы

### 1. **Неправильный тип обучения**
**Проблема:** Выбран художественный тип, но отправляется портретный
**Причина:** Дефолтное значение `training_type = "portrait"` в коде

### 2. **Неправильные параметры обучения**
**Проблема:** 2000 steps вместо правильных параметров для художественного типа
**Причина:** Используются настройки портретного тренера

### 3. **Ошибки webhook**
**Проблема:** "Failed to fetch training data" и "Failed to download archive"
**Причина:** Неправильная передача данных в FAL AI

### 4. **Только 20 шагов обучения**
**Проблема:** Обучение прерывается на 20 шагах
**Причина:** Ошибки в данных или конфигурации

## 🔧 Исправления

### 1. Исправление логики определения типа обучения

**Проблема в `app/handlers/avatar/training_production.py:85-90`:**
```python
# ПРОБЛЕМНЫЙ КОД:
training_type = getattr(avatar, 'training_type', 'portrait')  # ← Всегда портретный!
if hasattr(avatar, 'training_type') and avatar.training_type:
    training_type = avatar.training_type.value if hasattr(avatar.training_type, 'value') else str(avatar.training_type)
else:
    training_type = "portrait"  # ← Дефолт всегда портретный!
```

**ИСПРАВЛЕНИЕ:**
```python
# Получаем тип обучения из аватара (ИСПРАВЛЕНО)
if hasattr(avatar, 'training_type') and avatar.training_type:
    if hasattr(avatar.training_type, 'value'):
        training_type = avatar.training_type.value
    else:
        training_type = str(avatar.training_type)
    logger.info(f"🎯 Тип обучения из БД: {training_type}")
else:
    # Получаем из состояния FSM как fallback
    state_data = await state.get_data()
    training_type = state_data.get('training_type', 'portrait')
    logger.warning(f"⚠️ Тип обучения из состояния: {training_type}")
```

### 2. Исправление сохранения типа обучения в БД

**Проблема:** Тип обучения не сохраняется при создании аватара

**ИСПРАВЛЕНИЕ в создании аватара:**
```python
# При создании аватара сохранять training_type
avatar_data = {
    "name": name,
    "gender": gender,
    "training_type": training_type,  # ← ДОБАВИТЬ ЭТО
    "status": AvatarStatus.DRAFT
}
```

### 3. Исправление параметров обучения

**Проблема:** Неправильные параметры для художественного типа

**ИСПРАВЛЕНИЕ в `app/core/config.py`:**
```python
# Настройки для художественного обучения (flux-pro-trainer)
FAL_PRESET_BALANCED = {
    "portrait": {"steps": 1000, "learning_rate": 0.0002},
    "general": {
        "iterations": 500,        # ← НЕ steps!
        "learning_rate": 1e-4,    # ← Правильная скорость
        "priority": "quality"     # ← Приоритет качества
    }
}
```

### 4. Исправление URL данных для обучения

**Проблема:** Заглушка URL `https://example.com/photos/{avatar_id}.zip`

**ИСПРАВЛЕНИЕ:**
```python
# Получаем реальный URL архива с фотографиями
async with get_minio_service() as minio_service:
    training_data_url = await minio_service.get_avatar_photos_archive_url(avatar_id)
    
if not training_data_url:
    raise RuntimeError("Не удалось получить архив с фотографиями")
```

## 🚀 Применение исправлений

### Автоматическое исправление:
```bash
# 1. Диагностика проблем
chmod +x diagnose_avatar_training_issues.sh
./diagnose_avatar_training_issues.sh

# 2. Применение исправлений
chmod +x fix_avatar_training_issues.sh
./fix_avatar_training_issues.sh

# 3. Перезапуск сервисов
sudo systemctl restart aisha-bot.service aisha-api.service
```

### Ручная проверка:
```bash
# Проверить логи обучения
sudo journalctl -u aisha-bot.service -f | grep -E "(🎯|training_type|художественный)"

# Проверить webhook
sudo journalctl -u aisha-api.service -f | grep -E "(WEBHOOK|training_type)"

# Тест художественного обучения
curl -X POST http://localhost:8000/api/v1/avatar/status_update?training_type=style \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test_style", "status": "completed", "result": {"finetune_id": "test123"}}'
```

## ✅ Проверка исправлений

### 1. Тест выбора художественного типа:
- Создать новый аватар
- Выбрать "🎨 Художественный" тип
- Проверить в логах: `🎯 Запуск обучения аватара ... с типом: style`

### 2. Тест правильных параметров:
- Логи должны показывать: `🎨 Художественное обучение запущено`
- НЕ должно быть: `🎭 Портретное обучение запущено`

### 3. Тест webhook обработки:
- Webhook должен приходить с `training_type=style`
- Обработка должна использовать `flux-pro-trainer` логику

## 📊 Мониторинг

### Команды для отслеживания:
```bash
# Отслеживать типы обучения
sudo journalctl -u aisha-bot.service -f | grep -E "(🎯.*style|🎨.*Художественное)"

# Отслеживать webhook для художественных
sudo journalctl -u aisha-api.service -f | grep -E "(training_type=style|finetune_id)"

# Статистика типов обучения
sudo journalctl -u aisha-bot.service --since "1 day ago" | grep -c "тип: style"
sudo journalctl -u aisha-bot.service --since "1 day ago" | grep -c "тип: portrait"
```

## 🎯 Ожидаемые результаты после исправления

1. **✅ Художественный тип работает корректно**
2. **✅ Правильные параметры обучения (iterations вместо steps)**
3. **✅ Webhook обрабатывается с правильным типом**
4. **✅ Обучение завершается успешно с finetune_id**
5. **✅ Пользователи получают уведомления о готовности**

---

**🚀 После применения исправлений художественное обучение аватаров будет работать полностью!** 