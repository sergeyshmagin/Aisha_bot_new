# 🔌 Инструкция по настройке Telegram Bot Token

## 🚨 Проблема
При запуске бота возникает ошибка:
```
aiogram.utils.token.TokenValidationError: Token is invalid!
```

## 🔧 Решение

### Шаг 1: Получение токена от BotFather

1. **Открыть чат с BotFather**: [@BotFather](https://t.me/BotFather)

2. **Создать нового бота**:
   ```
   /newbot
   ```

3. **Указать название бота**:
   ```
   Aisha Assistant Bot
   ```

4. **Указать username бота** (должен заканчиваться на 'bot'):
   ```
   aisha_assistant_bot
   ```

5. **Скопировать полученный токен**:
   ```
   1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk
   ```

### Шаг 2: Настройка переменных окружения

**Файл: `.env`**
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk

# Database Configuration  
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aisha_bot

# Other settings...
```

### Шаг 3: Проверка формата токена

✅ **Правильный формат**:
```
1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk
```

❌ **Неправильные форматы**:
```
bot1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk  # Лишний префикс "bot"
1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk    # Неправильный разделитель
ABCDEFGHIJKLMNOPQRSTUVWXYZ                           # Слишком короткий
```

### Шаг 4: Валидация токена в коде

**Файл: `app/core/config.py`**
```python
from aiogram.utils.token import TokenValidationError
import re

def validate_bot_token(token: str) -> bool:
    """Валидация формата Telegram Bot Token"""
    if not token:
        return False
    
    # Формат: цифры:буквы_и_цифры_и_символы (длина >= 35)
    pattern = r'^\d+:[A-Za-z0-9_-]{35,}$'
    return bool(re.match(pattern, token))

# В настройках
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not validate_bot_token(TELEGRAM_BOT_TOKEN):
    raise ValueError(
        "❌ Неправильный формат TELEGRAM_BOT_TOKEN!\n"
        "Получите токен от @BotFather и добавьте в .env файл:\n"
        "TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
    )
```

## 🛠️ Дополнительные настройки бота

### Настройка команд через BotFather

1. **Установить команды**:
   ```
   /setcommands
   ```

2. **Выбрать бота**: `@aisha_assistant_bot`

3. **Добавить команды**:
   ```
   start - 🚀 Запустить бота
   help - ❓ Помощь
   profile - 👤 Профиль пользователя
   avatars - 🎭 Создание аватаров
   settings - ⚙️ Настройки
   ```

### Настройка описания бота

1. **Установить описание**:
   ```
   /setdescription
   ```

2. **Добавить описание**:
   ```
   🤖 Aisha - персональный ИИ-ассистент
   
   ✨ Возможности:
   • 🎭 Создание персональных аватаров
   • 💬 Умные диалоги
   • 🔊 Обработка аудио
   • 📝 Работа с текстом
   ```

### Настройка приватности

1. **Отключить группы** (если нужно только для личных чатов):
   ```
   /setjoingroups
   Disable
   ```

2. **Настроить приватность**:
   ```
   /setprivacy
   Disable
   ```

## 🧪 Тестирование

### Проверка подключения

**Файл: `test_bot_connection.py`**
```python
import asyncio
from aiogram import Bot
from app.core.config import settings

async def test_bot_connection():
    """Тест подключения к Telegram API"""
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        
        print(f"✅ Бот подключен успешно!")
        print(f"📝 Имя: {bot_info.first_name}")
        print(f"🏷️ Username: @{bot_info.username}")
        print(f"🆔 ID: {bot_info.id}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot_connection())
```

### Запуск теста
```bash
cd /c/dev/Aisha_bot_new
python test_bot_connection.py
```

**Ожидаемый результат**:
```
✅ Бот подключен успешно!
📝 Имя: Aisha Assistant Bot
🏷️ Username: @aisha_assistant_bot
🆔 ID: 1234567890
```

## 🚀 Запуск бота

### После настройки токена:

```bash
# Активация виртуального окружения
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# Запуск бота
python main.py
```

**Ожидаемый вывод**:
```
🤖 Starting Aisha Bot...
✅ Bot connected successfully!
📝 Bot name: Aisha Assistant Bot
🏷️ Username: @aisha_assistant_bot
🆔 Bot ID: 1234567890
🚀 Bot is running and listening for updates...
```

## 🔐 Безопасность

### Защита токена

1. **Никогда не коммитить токен** в Git:
   ```gitignore
   # .gitignore
   .env
   *.env
   .env.local
   .env.production
   ```

2. **Использовать переменные окружения**:
   ```python
   # ✅ Правильно
   TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
   
   # ❌ Неправильно
   TELEGRAM_BOT_TOKEN = "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
   ```

3. **Ротация токенов** при компрометации:
   ```
   /revoke
   /newtoken
   ```

## 📚 Полезные ссылки

- **[BotFather](https://t.me/BotFather)** - создание и управление ботами
- **[Telegram Bot API](https://core.telegram.org/bots/api)** - официальная документация
- **[aiogram](https://docs.aiogram.dev/)** - документация фреймворка

## ✅ Чек-лист настройки

- [ ] Получен токен от @BotFather
- [ ] Токен добавлен в `.env` файл
- [ ] Проверен формат токена (цифры:буквы_цифры_символы)
- [ ] Настроены команды бота
- [ ] Добавлено описание бота
- [ ] Проверено подключение через тест
- [ ] Токен не попал в Git (добавлен в .gitignore)
- [ ] Бот успешно запускается

---

**🎉 После выполнения всех шагов бот готов к работе!** 