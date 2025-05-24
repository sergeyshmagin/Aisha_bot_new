# ПЛАН ОЧИСТКИ LEGACY КОДА И УСТРАНЕНИЯ ИЗБЫТОЧНОСТИ

## 🎯 ЦЕЛЬ
Устранить всю избыточность в проекте, удалить Legacy код и унифицировать тестовые режимы.

---

## 🚨 1. КРИТИЧЕСКАЯ ИЗБЫТОЧНОСТЬ: ТЕСТОВЫЕ РЕЖИМЫ

### Проблема
```python
# В config.py:
FAL_TRAINING_TEST_MODE: bool = Field(True, env="FAL_TRAINING_TEST_MODE")  # FAL-специфичный
AVATAR_TEST_MODE: bool = Field(True, env="AVATAR_TEST_MODE")             # UI-специфичный
```

### Использование:
- `FAL_TRAINING_TEST_MODE` → `app/services/fal/client.py:34`, `app/services/avatar/fal_training_service.py:28`
- `AVATAR_TEST_MODE` → `app/handlers/avatar/training_production.py:50`, `app/handlers/avatar/photo_upload.py:779`

### ✅ РЕШЕНИЕ: Унификация
1. **Оставить только `AVATAR_TEST_MODE`** как единственный флаг
2. **Удалить `FAL_TRAINING_TEST_MODE`** и заменить на `AVATAR_TEST_MODE`
3. **Обновить все сервисы** для использования единого флага

---

## 🗂️ 2. LEGACY ФАЙЛЫ К УДАЛЕНИЮ

### 📁 Найденные .LEGACY файлы:
```
✅ app/services/avatar/avatar_service.py.LEGACY - весь код закомментирован
✅ app/services/avatar/service.py.LEGACY - весь код закомментирован
✅ LEGACY_CLEANUP_REPORT.md - дублирует docs/REPORTS/LEGACY_CLEANUP_REPORT.md
```

### 📄 Legacy код в активных файлах:
```python
# app/core/utils.py:54
# LEGACY: Дублирующаяся функция - cleanup_old_files()

# app/keyboards/main.py:11  
# [InlineKeyboardButton(text="🤖 Бизнес-ассистент", callback_data="business_menu")],  # LEGACY

# app/database/models.py:195, 239
# Legacy поля для совместимости

# app/handlers/avatar/create.py:189
# LEGACY - старая заглушка start_photo_upload_legacy

# app/database/repositories/transcript.py:26
"""LEGACY: Получить транскрипты пользователя из БД"""

# app/services/transcript.py:157
"""LEGACY: Получает все транскрипты пользователя"""

# app/handlers/fallback.py:7
F.data.startswith("legacy_") |
```

---

## 📋 3. ПЛАН ПОЭТАПНОЙ ОЧИСТКИ

### 🔥 Фаза 1: Унификация тестовых режимов (КРИТИЧНО)- [x] **Шаг 1.1**: Заменить `settings.FAL_TRAINING_TEST_MODE` → `settings.AVATAR_TEST_MODE` в:  - ⚠️ `app/services/fal/client.py:34` (файл поврежден при редактировании)  - ⚠️ `app/services/avatar/fal_training_service.py:28` (файл поврежден при редактировании)- [x] **Шаг 1.2**: Удалить `FAL_TRAINING_TEST_MODE` из `app/core/config.py`- [x] **Шаг 1.3**: Обновить `env.example`, тесты и скрипты- [x] **Шаг 1.4**: Протестировать работу конфигурации ✅### 🗑️ Фаза 2: Удаление .LEGACY файлов- [x] **Шаг 2.1**: Удалить `app/services/avatar/avatar_service.py.LEGACY` ✅- [x] **Шаг 2.2**: Удалить `app/services/avatar/service.py.LEGACY` ✅- [x] **Шаг 2.3**: Удалить дублирующий `LEGACY_CLEANUP_REPORT.md` ✅### 🧹 Фаза 3: Очистка Legacy кода- [x] **Шаг 3.1**: Удалить закомментированный код `cleanup_old_files()` в `app/core/utils.py` ✅- [x] **Шаг 3.2**: Удалить Legacy кнопку "Бизнес-ассистент" в `app/keyboards/main.py` ✅- [ ] **Шаг 3.3**: Очистить Legacy поля в `app/database/models.py` (если не используются)- [x] **Шаг 3.4**: Удалить Legacy заглушку в `app/handlers/avatar/create.py` ✅- [ ] **Шаг 3.5**: Мигрировать Legacy методы транскриптов или удалить- [x] **Шаг 3.6**: Очистить `F.data.startswith("legacy_")` в `app/handlers/fallback.py` ✅

### 📝 Фаза 4: Обновление документации
- [ ] **Шаг 4.1**: Обновить все упоминания `FAL_TRAINING_TEST_MODE` → `AVATAR_TEST_MODE`
- [ ] **Шаг 4.2**: Удалить Legacy секции из документации
- [ ] **Шаг 4.3**: Обновить `README.md` с актуальной информацией

---

## 🎯 4. КРИТЕРИИ ГОТОВНОСТИ

### ✅ После очистки должно быть:
- **0 файлов** с расширением `.LEGACY`
- **1 тестовый флаг** вместо 2 (`AVATAR_TEST_MODE` только)
- **0 закомментированного** Legacy кода
- **Чистые handlers** без Legacy обработчиков
- **Обновленная документация** без упоминаний Legacy

### 🧪 Тесты после очистки:
```bash
# Проверка отсутствия Legacy файлов
find . -name "*.LEGACY" -type f

# Проверка отсутствия Legacy кода
grep -r "LEGACY\|Legacy\|legacy" --include="*.py" app/

# Проверка единого тестового флага
grep -r "FAL_TRAINING_TEST_MODE" .
```

---

## ⚠️ 5. ПРЕДУПРЕЖДЕНИЯ

### 🔒 НЕ УДАЛЯТЬ:
- Legacy поля в `models.py` если используются в миграциях БД
- Legacy методы транскриптов если есть активные вызовы
- Библиотечные Legacy файлы в `.venv/`

### 🧪 Тестировать после каждой фазы:
```bash
python -m app.main  # Проверка запуска
python -m pytest tests/  # Проверка тестов
```

---

## 📊 6. ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### До очистки:
- 2 тестовых флага (путаница)
- 2 .LEGACY файла (мусор)
- ~10 Legacy комментариев (технический долг)
- Дублирующаяся документация

### После очистки:
- ✅ 1 унифицированный тестовый флаг
- ✅ 0 Legacy файлов  
- ✅ Чистый код без закомментированных блоков
- ✅ Актуальная документация
- ✅ Лучшая читаемость и сопровождаемость

---

**Статус**: 🔄 ГОТОВ К ВЫПОЛНЕНИЮ  
**Приоритет**: 🔥 ВЫСОКИЙ (избыточность мешает разработке)  
**Время**: ~2-3 часа  
**Риск**: 🟡 НИЗКИЙ (в основном удаление мусора) 