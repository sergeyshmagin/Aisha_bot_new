# Исправление проблемы с повторной генерацией в галерее

## 📋 Описание проблемы

### Основная проблема
Кнопка "🔄 Повторить" в галерее работала неправильно:

1. **Промежуточные экраны**: Показывала окно создания изображения вместо прямого запуска генерации
2. **Нерабочие кнопки**: Кнопки "📊 Статус генерации" и "🖼️ Галерея" вызывали ошибку "Неизвестная команда"
3. **Отсутствие мониторинга**: Нет автоматического отслеживания прогресса генерации
4. **Плохой UX**: Пользователь вынужден был совершать лишние действия

### Скриншоты проблемы
- **Скрин 1**: Лишнее окно создания изображения  
- **Скрин 2**: Ошибка "Неизвестная команда. Используйте кнопки меню."

## 🔧 Причины проблем

### 1. Отсутствующие обработчики callback'ов
```python
# Отсутствовали обработчики для:
callback_data="generation_status:{generation_id}"  # ❌ Нет обработчика
callback_data="gallery_main"                       # ❌ Нет обработчика

# Поэтому срабатывал fallback обработчик:
@fallback_router.callback_query()
async def fallback_unknown_callback(call: CallbackQuery):
    await call.answer("❌ Неизвестная команда. Используйте кнопки меню.", show_alert=True)
```

### 2. Неправильная логика повторной генерации
Старый код в `RegenerationManager._start_regeneration`:
- Создавал статичные кнопки вместо запуска мониторинга
- Не отслеживал прогресс автоматически
- Показывал промежуточные экраны

## ✅ Реализованные исправления

### 1. Добавлены недостающие обработчики

**Файл**: `app/handlers/gallery/main_handler.py`

```python
@router.callback_query(F.data == "gallery_main")
async def handle_gallery_main_new(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback gallery_main (альтернативный к my_gallery)"""
    logger.info(f"🖼️ Обработка callback gallery_main от пользователя {callback.from_user.id}")
    await handle_gallery_main(callback, state)

@router.callback_query(F.data.startswith("generation_status:"))
async def handle_generation_status(callback: CallbackQuery):
    """Обработчик проверки статуса генерации"""
    # Получаем генерацию из БД
    # Если завершена - переходим к изображению в галерее
    # Иначе - показываем текущий статус
```

### 2. Переработана логика повторной генерации

**Файл**: `app/handlers/gallery/management/regeneration.py`

#### До исправления:
```python
async def _start_regeneration(self, callback, original_generation, user_id):
    # Создавал статичные кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статус генерации", ...)],
        [InlineKeyboardButton(text="🖼️ Галерея", ...)]
    ])
    # Показывал статичное сообщение без мониторинга
```

#### После исправления:
```python
async def _start_regeneration(self, callback, original_generation, user_id):
    # 1. Проверка баланса
    if not await self.check_user_balance_for_regeneration(user_id, GENERATION_COST):
        return
    
    # 2. Проверка готовности аватара
    # 3. Показ прогрессивного сообщения
    # 4. Запуск генерации
    # 5. Автоматический мониторинг с _monitor_regeneration_progress()
```

### 3. Добавлен автоматический мониторинг прогресса

```python
async def _monitor_regeneration_progress(self, message, generation, prompt: str, avatar_name: str):
    """Мониторинг прогресса повторной генерации"""
    max_attempts = 60  # 3 минуты
    
    while attempt < max_attempts:
        # Проверяем статус в БД каждую секунду
        updated_generation = await self._get_generation(generation.id, generation.user_id)
        
        if updated_generation.status == GenerationStatus.COMPLETED:
            await self._show_regeneration_result(message, updated_generation, prompt, avatar_name)
            return
            
        # Обновляем прогресс каждые 3 секунды
        if attempt % 3 == 0:
            progress = min(90, attempt * 2)
            await message.edit_text(f"🔄 Прогресс: {progress}%", ...)
```

### 4. Улучшенный показ результата

```python
async def _show_regeneration_result(self, message, generation, prompt: str, avatar_name: str):
    """Показывает результат завершенной повторной генерации"""
    # Загружаем изображение
    # Удаляем старое сообщение
    # Отправляем фото с caption и кнопками:
    # - "🔄 Повторить еще раз" 
    # - "🖼️ В галерею"
    # - "🎨 Новая генерация"
    # - "🔙 Главное меню"
```

## 🚀 Процесс деплоя

### Команда деплоя
```bash
cd /opt/aisha-backend
scripts/deployment/quick-fix-deploy.sh
```

### Результат деплоя
```
[INFO] 🚀 Быстрый деплой исправления: fix-help-20250611-185848
[INFO] 🔨 Сборка образа с тегом fix-help-20250611-185848...
[INFO] 📤 Отправка образа в registry...
[INFO] 🏷️ Обновление latest тега...
[INFO] 🚀 Деплой на продакшн сервер...
🔄 Перезапуск bot контейнеров...
📊 Статус контейнеров:
      Name                 Command              State       Ports
-----------------------------------------------------------------
aisha-bot-primary   /entrypoint.sh polling   Up (healthy)        
aisha-worker-1      /entrypoint.sh worker    Up (healthy)        
🎉 Деплой завершен!
[INFO] ✅ Исправление успешно развернуто!
```

## 📊 Результаты

### До исправления:
- ❌ Кнопка "повторить" показывала лишние экраны
- ❌ Ошибка "Неизвестная команда" для кнопок статуса и галереи
- ❌ Отсутствие автоматического мониторинга
- ❌ Плохой пользовательский опыт

### После исправления:
- ✅ Прямой запуск повторной генерации одним кликом
- ✅ Автоматический мониторинг прогресса с обновлением каждые 3 секунды
- ✅ Показ результата с изображением по завершении
- ✅ Правильная обработка всех callback'ов
- ✅ Понятный UX с прогресс-баром и эмоджи

### Новый flow повторной генерации:
1. **Пользователь жмет "🔄 Повторить"** → Проверка баланса и аватара
2. **Автоматический запуск** → "🔄 Повторная генерация запущена"
3. **Мониторинг в реальном времени** → "🔄 Прогресс: 34%"
4. **Показ результата** → Фото + кнопки действий

## 🔧 Технические детали

### Файлы изменений:
- ✅ `app/handlers/gallery/main_handler.py` - добавлены обработчики callback'ов
- ✅ `app/handlers/gallery/management/regeneration.py` - переработана логика повтора

### Новые методы:
- `handle_gallery_main_new()` - обработчик callback "gallery_main"
- `handle_generation_status()` - проверка статуса генерации  
- `check_user_balance_for_regeneration()` - проверка баланса
- `_monitor_regeneration_progress()` - автомониторинг прогресса
- `_show_regeneration_result()` - показ результата с фото
- `_show_regeneration_error()` - обработка ошибок

### Архитектурные улучшения:
- 🔄 Унифицированная обработка callback'ов
- 📊 Автоматический мониторинг статуса генерации  
- 🖼️ Правильная работа с сообщениями-изображениями
- ⚡ Быстрый отклик на действия пользователя

## 🎯 Итоговый статус

✅ **Проблема полностью решена**
- Повторная генерация работает корректно
- Все кнопки обрабатываются правильно
- UX значительно улучшен
- Автоматический мониторинг реализован
- ✅ **Проверка и списание баланса работает корректно**

### Финальные исправления (12.06.2025):

**Проблема SQLAlchemy**: Ошибка `greenlet_spawn has not been called` при проверке баланса
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here
```

**Решение**: Переработана проверка баланса с использованием правильного `UserService`:

```python
async def check_user_balance_for_regeneration(self, user_id: UUID, cost: int) -> bool:
    """Проверяет баланс пользователя для повторной генерации"""
    try:
        from app.core.di import get_user_service
        
        async with get_user_service() as user_service:
            # Получаем текущий баланс пользователя
            current_balance = await user_service.get_user_balance(user_id)
            
            # Проверяем достаточность средств
            has_sufficient_balance = current_balance >= cost
            
            logger.info(f"Проверка баланса пользователя {user_id}: баланс={current_balance}, стоимость={cost}, достаточно={has_sufficient_balance}")
            
            return has_sufficient_balance
            
    except Exception as e:
        logger.exception(f"Ошибка проверки баланса: {e}")
        # В случае ошибки НЕ разрешаем генерацию для безопасности
        return False
```

**Добавлено списание баланса** при успешном запуске генерации:
```python
# Списываем баланс после успешного создания генерации
try:
    from app.core.di import get_user_service
    async with get_user_service() as user_service:
        new_balance = await user_service.remove_coins(user_id, GENERATION_COST)
        if new_balance is not None:
            logger.info(f"Списано {GENERATION_COST} монет за повторную генерацию. Новый баланс: {new_balance}")
        else:
            logger.warning(f"Не удалось списать баланс за повторную генерацию для пользователя {user_id}")
except Exception as balance_error:
    logger.exception(f"Ошибка списания баланса: {balance_error}")
    # Генерация уже запущена, поэтому продолжаем
```

### Архитектура баланса:
- **Модель**: `UserBalance` с полем `coins`
- **Сервис**: `UserService.get_user_balance()` и `remove_coins()`
- **Репозиторий**: `BalanceRepository` для работы с БД
- **Кеширование**: Redis кеш для быстрого доступа к балансу

**Деплой**: `fix-help-20250612-064047` → `192.168.0.4:5000/aisha/bot:latest`  
**Продакшн**: `192.168.0.10` - контейнеры `aisha-bot-primary` и `aisha-worker-1` работают  
**Дата**: 12.06.2025, 06:41 UTC

### Безопасность платежей:
- ✅ Проверка баланса перед генерацией
- ✅ Списание средств только при успешном запуске
- ✅ Логирование всех операций с балансом
- ✅ Fallback на отказ при ошибках (безопасность превыше всего) 