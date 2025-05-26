# Исправления и решения проблем

## ✅ Проблема с полем `order` в таблице `avatar_photos`

### **Описание проблемы**
```
sqlalchemy.exc.IntegrityError: null value in column "order" of relation "avatar_photos" violates not-null constraint
```

### **Причина**
Несоответствие между моделью SQLAlchemy и структурой базы данных:
- **Код**: использует поле `upload_order`
- **База данных**: ожидает поле `order` с NOT NULL constraint

### **Решение**
1. **Временная совместимость**: Добавлено поле `order` в модель для работы с существующей БД
2. **Прямое удаление колонки**: Создан скрипт `scripts/remove_order_column.py` для удаления колонки из БД
3. **Очистка кода**: Удалены временные поля после успешного удаления колонки

### **Применённые файлы**
- `app/database/models.py` - модель `AvatarPhoto`
- `app/services/avatar/photo_service.py` - сервис загрузки фото
- `scripts/remove_order_column.py` - скрипт удаления колонки

### **Команды для исправления**
```bash
python scripts/remove_order_column.py
```

---

## ✅ Проблема с обработкой None в message.text

### **Описание проблемы**
```
AttributeError: 'NoneType' object has no attribute 'strip'
```

### **Причина**
Обработчик `process_avatar_name` пытался вызвать `.strip()` на `message.text`, который может быть `None` если пользователь отправил не-текстовое сообщение.

### **Решение**
Добавлена проверка на `None` перед обработкой текста:
```python
if not message.text:
    await message.answer(
        "❌ Пожалуйста, отправьте имя аватара текстом.\n"
        "Не используйте стикеры, фото или другие файлы."
    )
    return
```

### **Применённые файлы**
- `app/handlers/avatar/create.py` - обработчик создания аватара

---

## 🔧 Рекомендации

### **Предотвращение подобных проблем**
1. **Всегда применяйте миграции** перед удалением полей из моделей
2. **Используйте `alembic revision --autogenerate`** для автоматического создания миграций
3. **Тестируйте изменения** на development окружении
4. **Добавляйте проверки на None** для всех пользовательских вводов

### **Процесс работы с миграциями**
```bash
# 1. Создание миграции
alembic revision --autogenerate -m "описание_изменений"

# 2. Проверка миграции
alembic show

# 3. Применение миграции
alembic upgrade head

# 4. Проверка текущего состояния
alembic current
``` 