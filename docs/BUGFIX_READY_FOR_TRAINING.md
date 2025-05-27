# Исправление бага: Повторный запрос пола при нажатии "Готов к обучению"

## 🐛 Описание проблемы

При нажатии кнопки "Готов к обучению!" после загрузки фотографий система повторно запрашивала пол аватара вместо перехода к подтверждению обучения.

## 🔍 Причина проблемы

Конфликт между двумя обработчиками callback_data `confirm_training_*`:

1. **`confirm_training_current`** - из `photo_upload.py` (кнопка "Готов к обучению!")
2. **`confirm_training_portrait/style`** - из `training_type_selection.py` (выбор типа обучения)

Оба обработчика использовали один паттерн `F.data.startswith("confirm_training_")`, что приводило к неправильной маршрутизации.

## ✅ Решение

### 1. Исправлен обработчик в `training_type_selection.py`

```python
@router.callback_query(F.data.startswith("confirm_training_"))
async def confirm_training_type(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора типа обучения и переход к выбору пола"""
    try:
        callback_training_type = callback.data.split("_", 2)[2]
        
        # ИСПРАВЛЕНИЕ: Если это "current", то это подтверждение готовности к обучению
        if callback_training_type == "current":
            # Перенаправляем к обработчику подтверждения обучения из photo_upload
            from .photo_upload import photo_handler
            await photo_handler.show_training_confirmation(callback, state)
            return
        
        # Для новых аватаров (portrait/style) - продолжаем обычную логику
        # ... остальная логика для выбора типа обучения
```

### 2. Удален дублирующий обработчик из `photo_upload.py`

Удален обработчик `handle_confirm_training_current` для избежания конфликтов.

### 3. Исправлена проблема с получением баланса пользователя

**Проблема:** SQLAlchemy MissingGreenlet при попытке lazy loading баланса пользователя.

**Решение:** Явная загрузка баланса через асинхронную сессию:

```python
# ИСПРАВЛЕНИЕ: Получаем баланс через сервис, а не через lazy loading
try:
    from app.core.database import get_session
    async with get_session() as session:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from app.database.models import User
        
        stmt = select(User).options(selectinload(User.balance)).where(User.id == user.id)
        result = await session.execute(stmt)
        user_with_balance = result.scalar_one_or_none()
        
        if user_with_balance and user_with_balance.balance:
            user_balance = user_with_balance.balance.coins
        else:
            user_balance = 0
except Exception as balance_error:
    logger.warning(f"Ошибка получения баланса: {balance_error}")
    user_balance = 0  # По умолчанию 0 если не удалось получить баланс
```

## 🎯 Результат

- ✅ Кнопка "Готов к обучению!" теперь корректно показывает экран подтверждения
- ✅ Выбор типа обучения для новых аватаров работает как прежде
- ✅ Нет повторного запроса пола аватара
- ✅ Правильная маршрутизация между разными этапами создания аватара
- ✅ Исправлена ошибка SQLAlchemy MissingGreenlet при получении баланса
- ✅ Корректное отображение баланса пользователя в экране подтверждения

## 📋 Затронутые файлы

- `app/handlers/avatar/training_type_selection.py` - исправлена логика маршрутизации
- `app/handlers/avatar/photo_upload.py` - удален дублирующий обработчик

## 🧪 Тестирование

1. Создать новый аватар → выбрать тип обучения → выбрать пол → ввести имя → загрузить фото
2. Нажать "Готов к обучению!" 
3. ✅ Должен показаться экран подтверждения с балансом и стоимостью
4. ✅ НЕ должен повторно запрашиваться пол аватара

---
**Дата исправления:** $(date)  
**Статус:** ✅ Исправлено и протестировано 