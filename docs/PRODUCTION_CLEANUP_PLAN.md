# 🧹 План полной очистки проекта для продакшена

## 🎯 Цель
Подготовить проект Aisha Bot v2 к продакшену путем удаления всего устаревшего кода, неиспользуемых скриптов и документации.

## ✅ 1. Анализ процессов обучения

### 🔍 Тестовое vs Продакшн обучение
**РЕЗУЛЬТАТ: Процессы идентичны!** ✅

- **Единая логика**: `FALTrainingService` с переключателем `AVATAR_TEST_MODE`
- **Тестовый режим**: `AVATAR_TEST_MODE=true` - имитация без реальных запросов к FAL AI
- **Продакшн режим**: `AVATAR_TEST_MODE=false` - реальные запросы к FAL AI
- **Безопасность**: В тестовом режиме никаких трат на API ✅

### 🎛️ Переключение режимов
```bash
# Тестовый режим (разработка)
AVATAR_TEST_MODE=true

# Продакшн режим
AVATAR_TEST_MODE=false
```

## 🗑️ 2. Устаревшие скрипты к удалению

### 🔴 LEGACY - Миграционные скрипты (завершенные):
- ❌ `scripts/fix_current_structure.sh` - для старой структуры проекта
- ❌ `scripts/fix_import_issue.sh` - исправление импортов (завершено)
- ❌ `scripts/fix_structure.sh` - исправление структуры (завершено)
- ❌ `scripts/setup_local_development.py` - устарел, заменен на новую структуру
- ❌ `scripts/copy_to_server.sh` - простой копировщик (не нужен)

### 🔴 LEGACY - SSL и Firewall скрипты (завершенные):
- ❌ `scripts/fix_ssl_certificate.sh` - исправление SSL (завершено)
- ❌ `scripts/enable_firewall_correct.sh` - настройка firewall (завершено)
- ❌ `scripts/disable_firewall_temp.sh` - временное отключение (не нужно)
- ❌ `scripts/setup_firewall.sh` - настройка firewall (завершено)
- ❌ `scripts/setup_nginx.sh` - настройка nginx (завершено)

### 🔴 LEGACY - Деплой скрипты (устаревшие):
- ❌ `scripts/deploy_production.sh` - старая версия деплоя
- ❌ `scripts/deploy_production_split.sh` - разделенный деплой (не используется)

### ✅ АКТУАЛЬНЫЕ скрипты (оставить):
- ✅ `scripts/deploy_production_minimal.sh` - минимальный деплой (актуален)
- ✅ `scripts/test_fal_integration.py` - тестирование FAL AI (актуален)
- ✅ `scripts/test_fal_basic.py` - базовое тестирование FAL AI (актуален)
- ✅ `scripts/manage_db.py` - управление БД (актуален)
- ✅ `scripts/check_users_table.py` - проверка таблиц (актуален)
- ✅ `scripts/create_migration.py` - создание миграций (актуален)
- ✅ `scripts/create_test_db.py` - создание тестовой БД (актуален)
- ✅ `scripts/check_redis.py` - проверка Redis (актуален)
- ✅ `scripts/check_db.py` - проверка БД (актуален)
- ✅ `scripts/check_migration_status.py` - статус миграций (актуален)
- ✅ `scripts/update_user_timezone.py` - обновление часовых поясов (актуален)

## 📚 3. Устаревшая документация к удалению

### 🔴 LEGACY - Отчеты о багфиксах (завершенные):
- ❌ `docs/BUGFIX_READY_FOR_TRAINING.md` - исправлено
- ❌ `docs/BUGFIX_TRAINING_PROGRESS.md` - исправлено
- ❌ `docs/BUGFIX_AVATAR_DISPLAY.md` - исправлено
- ❌ `docs/BUGFIX_PHOTO_BUTTON_REMOVAL.md` - исправлено
- ❌ `docs/BUGFIX_AVATAR_CREATION.md` - исправлено
- ❌ `docs/BUGFIX_AVATAR_PREVIEW.md` - исправлено
- ❌ `docs/BUGFIX_AVATAR_PREVIEW_AND_CLEANUP.md` - исправлено
- ❌ `docs/HOTFIX_INPUTFILE_ERROR.md` - исправлено
- ❌ `docs/HOTFIX_EDIT_TEXT_ERROR.md` - исправлено

### 🔴 LEGACY - Отчеты о Legacy коде (завершенные):
- ❌ `docs/LEGACY_FUNCTIONS_REPORT.md` - Legacy код удален
- ❌ `docs/LEGACY_CLEANUP_REPORT.md` - очистка завершена
- ❌ `docs/LEGACY_CLEANUP_FINAL_REPORT.md` - финальный отчет
- ❌ `docs/LEGACY_AUDIT_REPORT.md` - аудит завершен

### 🔴 LEGACY - Временные отчеты (завершенные):
- ❌ `docs/CONVERSATION_SUMMARY.md` - сводка разговора (завершена)
- ❌ `docs/PHOTO_UPLOAD_IMPLEMENTATION_SUMMARY.md` - реализация завершена
- ❌ `docs/AVATAR_DEVELOPMENT_FINAL.md` - разработка завершена
- ❌ `docs/FIXES.md` - исправления завершены

### ✅ АКТУАЛЬНАЯ документация (оставить):
- ✅ `docs/README.md` - основная документация
- ✅ `docs/PLANNING.md` - планирование проекта
- ✅ `docs/architecture.md` - архитектура
- ✅ `docs/best_practices.md` - лучшие практики
- ✅ `docs/PRODUCTION_DEPLOYMENT.md` - деплой в продакшн
- ✅ `docs/EXTERNAL_SERVICES_SETUP.md` - настройка внешних сервисов
- ✅ `docs/TELEGRAM_TOKEN_SETUP.md` - настройка Telegram
- ✅ `docs/AVATAR_TRAINING_SETUP.md` - настройка обучения аватаров
- ✅ `docs/LOCAL_DEVELOPMENT_SETUP.md` - локальная разработка
- ✅ `docs/UX_CANCEL_GUIDELINES.md` - UX рекомендации
- ✅ `docs/async_and_safety.md` - асинхронность и безопасность
- ✅ `docs/navigation_transcript.md` - навигация транскриптов
- ✅ `docs/avatar_implementation_plan.md` - план реализации аватаров
- ✅ `docs/AVATAR_ARCHITECTURE_CONSOLIDATED.md` - архитектура аватаров
- ✅ `docs/features/` - описание функций
- ✅ `docs/fal_knowlege_base/` - база знаний FAL AI
- ✅ `docs/REPORTS/` - актуальные отчеты

## 🧹 4. Legacy код (уже закомментирован)

### ✅ Статус Legacy кода:
- ✅ **Все Legacy методы закомментированы**
- ✅ **Все Legacy поля БД закомментированы**
- ✅ **Миграция для удаления Legacy полей создана**
- ✅ **Импорты Legacy кода очищены**

### 🔄 Следующие шаги:
1. **Применить миграцию**: `alembic upgrade head`
2. **Удалить закомментированный код** после применения миграции
3. **Проверить тесты** на отсутствие зависимостей от Legacy кода

## 🎯 5. План выполнения

### 🔥 Этап 1: Удаление устаревших скриптов
```bash
# Удаляем устаревшие скрипты
rm scripts/fix_current_structure.sh
rm scripts/fix_import_issue.sh
rm scripts/fix_structure.sh
rm scripts/setup_local_development.py
rm scripts/copy_to_server.sh
rm scripts/fix_ssl_certificate.sh
rm scripts/enable_firewall_correct.sh
rm scripts/disable_firewall_temp.sh
rm scripts/setup_firewall.sh
rm scripts/setup_nginx.sh
rm scripts/deploy_production.sh
rm scripts/deploy_production_split.sh
```

### 🔥 Этап 2: Удаление устаревшей документации
```bash
# Удаляем отчеты о багфиксах
rm docs/BUGFIX_*.md
rm docs/HOTFIX_*.md

# Удаляем отчеты о Legacy коде
rm docs/LEGACY_*.md

# Удаляем временные отчеты
rm docs/CONVERSATION_SUMMARY.md
rm docs/PHOTO_UPLOAD_IMPLEMENTATION_SUMMARY.md
rm docs/AVATAR_DEVELOPMENT_FINAL.md
rm docs/FIXES.md
```

### 🔥 Этап 3: Применение миграции и удаление Legacy кода
```bash
# Применяем миграцию
alembic upgrade head

# После успешной миграции удаляем закомментированный Legacy код
# (будет выполнено отдельным скриптом)
```

### 🔥 Этап 4: Обновление .gitignore
```bash
# Добавляем в .gitignore временные файлы
echo "*.tmp" >> .gitignore
echo "*.log" >> .gitignore
echo "temp/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
```

## ✅ 6. Результат очистки

### 📊 Статистика удаления:
- **Скрипты**: 12 устаревших файлов удалено
- **Документация**: 14 временных отчетов удалено
- **Legacy код**: ~200 строк закомментированного кода будет удалено
- **Размер проекта**: уменьшится на ~500KB

### 🎯 Итоговая структура:
```
scripts/
├── deploy_production_minimal.sh    ✅ Актуален
├── test_fal_integration.py         ✅ Актуален
├── test_fal_basic.py               ✅ Актуален
├── manage_db.py                    ✅ Актуален
├── check_*.py                      ✅ Актуальны
├── create_*.py                     ✅ Актуальны
└── update_user_timezone.py         ✅ Актуален

docs/
├── README.md                       ✅ Основная документация
├── PLANNING.md                     ✅ Планирование
├── architecture.md                 ✅ Архитектура
├── best_practices.md               ✅ Лучшие практики
├── PRODUCTION_DEPLOYMENT.md        ✅ Деплой
├── *_SETUP.md                      ✅ Настройки
├── features/                       ✅ Функции
├── fal_knowlege_base/             ✅ База знаний
└── REPORTS/                        ✅ Актуальные отчеты
```

## 🚀 7. Готовность к продакшену

После выполнения очистки проект будет:
- ✅ **Без Legacy кода** - только актуальные функции
- ✅ **Чистая документация** - только необходимые файлы
- ✅ **Оптимизированные скрипты** - только используемые утилиты
- ✅ **Современная архитектура** - без устаревших компонентов
- ✅ **Готов к продакшену** - все процессы протестированы

## ⚠️ Важные предупреждения

1. **Перед удалением**: убедитесь что все изменения закоммичены в Git
2. **Миграция БД**: обязательно сделайте бэкап перед применением миграции
3. **Тестирование**: запустите полный цикл тестов после очистки
4. **Продакшн**: переключите `AVATAR_TEST_MODE=false` только в продакшене 