# План консолидации документации

## 🎯 Цель
Упростить структуру документации, удалив дублирование и оставив только актуальную информацию.

## 📋 Основные документы (оставить)

### Технические
- ✅ `README.md` - Основная информация
- ✅ `CHANGELOG.md` - История изменений  
- ✅ `FEATURES.md` - Описание функций
- ✅ `architecture.md` - Архитектура системы
- ✅ `best_practices.md` - Лучшие практики
- ✅ `DEPLOYMENT.md` - Инструкции по развертыванию
- ✅ `TROUBLESHOOTING.md` - Устранение неисправностей

### Справочные
- ✅ `INDEX.md` - Навигация по документации
- ✅ `PROJECT_STATUS.md` - Текущий статус
- ✅ `PROJECT_CLEANUP_ANALYSIS.md` - Анализ очистки

## 🗑️ Файлы для удаления

### UX документы (дублируют друг друга)
- ❌ `UX_FIXES_SUMMARY.md`
- ❌ `UX_IMPROVEMENTS_CHANGELOG.md` 
- ❌ `UX_IMPROVEMENTS_FINAL.md`
- ❌ `UX_ANALYSIS_FINAL.md`
- ❌ `UX_CHANGES_SUMMARY.md`
- ❌ `UX_FLOW_NEW.md`
- ❌ `UX_ANALYSIS_PROFILE_DUPLICATION.md`
- ❌ `UX_AUDIT_40PLUS.md`

### Menu документы (консолидированы в FEATURES.md)
- ❌ `MENU_IMPROVEMENTS_SUMMARY.md`
- ❌ `MENU_REFACTORING_COMPLETE.md`
- ❌ `MENU_REFACTORING_FINAL.md`
- ❌ `MENU_REFACTORING_PLAN.md`
- ❌ `MENU_REFACTORING_RESULTS.md`
- ❌ `MENU_MAPPING.md`
- ❌ `OPTIMIZED_USER_FLOW.md`

### Callback документы (устарели)
- ❌ `CALLBACK_COMPLETION_FINAL.md`
- ❌ `CALLBACK_ERRORS_FIXED.md`
- ❌ `CALLBACK_HANDLERS_COMPLETE.md`
- ❌ `BUTTON_HANDLERS_FIX.md`
- ❌ `CHANGELOG_MENU_FIX.md`

### Галерея документы (информация в CHANGELOG.md)
- ❌ `GALLERY_EMPTY_MENU_UPDATE.md`
- ❌ `GALLERY_FILTERS_IMPLEMENTATION.md`
- ❌ `NAVIGATION_FIX_IMAGEN4.md`

### Imagen4 документы (часть информации в FEATURES.md)
- ❌ `IMAGEN4_DISCUSSION_SUMMARY.md`
- ❌ `IMAGEN4_MINIO_REDIS_FIXES.md`
- ❌ `PLAN_IMAGEN4_INTEGRATION.md`

### Прочие специфичные документы
- ❌ `BUGFIXES.md` (информация в CHANGELOG.md)
- ❌ `BUSINESS_FEATURES.md` (информация в FEATURES.md)
- ❌ `EYE_QUALITY_IMPROVEMENTS.md` (устарело)
- ❌ `USER_FRIENDLY_MESSAGES.md` (устарело)
- ❌ `WELCOME_MESSAGE_UPDATE.md` (устарело)
- ❌ `PROFILE_MIGRATION_COMPLETE.md` (выполнено)
- ❌ `MIGRATION_SUMMARY.md` (устарело)
- ❌ `TERMINOLOGY_UPDATE_FOTO_SO_MNOY.md` (выполнено)
- ❌ `IMPLEMENTATION_PLAN.md` (устарело)
- ❌ `INTEGRATION_CHANGELOG.md` (в CHANGELOG.md)
- ❌ `LEGACY_CLEANUP_PLAN.md` (выполнено)

### Deployment документы (консолидировать)
- Оставить: `DEPLOYMENT.md`
- ❌ `DEPLOYMENT_SUCCESS.md` 
- ❌ `WEBHOOK_DEPLOYMENT.md`
- ❌ `DOCKER_ARCHITECTURE.md` (информация в architecture.md)

## 📁 Структура папок

### Оставить как есть
- `setup/` - Инструкции по настройке
- `development/` - Документация разработки  
- `reference/` - Справочные материалы
- `features/` - Детальное описание функций
- `fixes/` - История исправлений

## 🧹 План выполнения

1. **Создать резервную копию** всех документов
2. **Удалить избыточные файлы** по списку выше
3. **Обновить INDEX.md** с новой структурой
4. **Проверить ссылки** в оставшихся документах
5. **Коммит изменений**

## ✅ Ожидаемый результат

- Документация уменьшена до ~15 основных файлов
- Убрано дублирование информации
- Легкая навигация и поиск
- Актуальная информация в ключевых документах 