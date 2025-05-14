# Быстрый старт (Quickstart)

## 1. Установка и запуск

```bash
pip install -r requirements.txt
```

Установите ffmpeg (Linux: `sudo apt install ffmpeg`, Windows: [скачать](https://ffmpeg.org/download.html)).

Создайте файл `.env`:

```env
TELEGRAM_TOKEN=ваш_токен
OPENAI_API_KEY=ваш_openai_ключ
STORAGE_DIR=storage
```

Запустите бота:

```bash
python -m frontend_bot.main
```

---

## 2. Пример добавления нового шаблона сообщения

Откройте `frontend_bot/texts/common.py` и добавьте:

```python
NEW_FEATURE_TEXT = "Текст для новой фичи..."
```

Используйте этот шаблон в хендлере или сервисе:

```python
from frontend_bot.texts.common import NEW_FEATURE_TEXT
await bot.send_message(chat_id, NEW_FEATURE_TEXT)
```

---

## 3. Пример добавления новой клавиатуры

Откройте `frontend_bot/keyboards/common.py` и добавьте:

```python
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def new_feature_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Кнопка", callback_data="new_feature"))
    return keyboard
```

Используйте клавиатуру:

```python
from frontend_bot.keyboards.common import new_feature_keyboard
await bot.send_message(chat_id, "Выберите действие:", reply_markup=new_feature_keyboard())
```

---

## 4. Пример асинхронной работы с файлами

```python
import aiofiles

async def read_file_async(path: str) -> str:
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()
```

---

## 5. Ссылки

- [Архитектура проекта](architecture.md)
- [Best Practices](best_practices.md)
- [Асинхронность и безопасность](async_and_safety.md)
