# Навигация в модуле транскрибации

## Архитектура навигации

```
Главное меню приложения
      ↓ (transcribe_menu)
Меню транскрибации
      ↓ (transcribe_history)
История транскриптов
      ↓ (transcribe_open_{id})
Карточка транскрипта
```

## Кнопки и их назначение

### В главном меню приложения
- **🎤 Транскрибация** → `transcribe_menu` → переход в меню транскрибации

### В меню транскрибации
- **🎤 Аудио** → `transcribe_audio` → ожидание аудио
- **📝 Текст** → `transcribe_text` → ожидание текста  
- **📜 История** → `transcribe_history` → список транскриптов
- **◀️ Назад** → `back_to_main` → возврат в главное меню приложения

### В истории транскриптов
- **[Транскрипт]** → `transcribe_open_{id}` → открытие карточки
- **⬅️ Назад / Вперёд ➡️** → `transcribe_history_page_{n}` → пагинация
- **◀️ Назад в меню** → `transcribe_back_to_menu` → возврат в меню транскрибации

### На карточке транскрипта
- **📝 Краткое содержание** → `transcript_summary_{id}` → обработка GPT
- **✅ Список задач** → `transcript_todo_{id}` → обработка GPT  
- **📊 Протокол** → `transcript_protocol_{id}` → обработка GPT
- **⬅️ Назад** → `transcribe_history` → возврат в историю
- **🏠 В меню** → `transcribe_back_to_menu` → возврат в меню транскрибации

### В состояниях ожидания аудио/текста
- **◀️ Назад в меню** → `transcribe_back_to_menu` → возврат в меню транскрибации

## Обработчики callback

### transcript_main.py
- `transcribe_audio` → установка состояния ожидания аудио
- `transcribe_text` → установка состояния ожидания текста
- `transcribe_history` → показ истории транскриптов
- `transcribe_back_to_menu` → возврат в меню транскрибации
- `transcribe_history_page_{n}` → пагинация истории
- `transcribe_open_{id}` → открытие карточки транскрипта

### main_menu.py  
- `back_to_main` → возврат в главное меню приложения
- `transcribe_menu` → переход в меню транскрибации

### transcript_processing.py
- `transcript_summary_{id}` → генерация краткого содержания
- `transcript_todo_{id}` → генерация списка задач
- `transcript_protocol_{id}` → генерация протокола

## UX принципы

1. **Кнопка "Назад"** всегда возвращает на предыдущий уровень иерархии
2. **Кнопка "В меню"** возвращает в меню текущего модуля (транскрибация)
3. **Кнопка "Назад в меню"** используется из вложенных состояний
4. **Защита от ошибок редактирования**: если сообщение нельзя отредактировать (содержит документ), отправляется новое сообщение

## Решенные проблемы

- ❌ "Bad Request: there is no text in the message to edit" → ✅ try/catch с fallback на новое сообщение
- ❌ Кнопка "Назад" с карточки возвращала в меню → ✅ возвращает в историю  
- ❌ Неправильная обработка callback `transcribe_back_to_menu` → ✅ отдельный обработчик
- ❌ "BaseModel.__init__() takes 1 positional argument but 2 were given" → ✅ исправлены типы user_id в репозитории

## Технические детали исправлений

### Проблема с типами user_id
**Ошибка**: `BaseModel.__init__() takes 1 positional argument but 2 were given`

**Причина**: В `TranscriptRepository` методы принимали `user_id: int`, но сервис передавал `UUID`.

**Решение**: Обновлены типы в репозитории:
```python
# Было:
async def get_user_transcripts(self, user_id: int, limit: int = 10, offset: int = 0)

# Стало:
async def get_user_transcripts(self, user_id: Union[int, str, UUID], limit: int = 10, offset: int = 0)
```

### Защита от ошибок редактирования сообщений
```python
try:
    await call.message.edit_text(text, reply_markup=keyboard)
except Exception as edit_error:
    # Fallback на новое сообщение если редактирование невозможно
    await call.message.answer(text, reply_markup=keyboard)
``` 