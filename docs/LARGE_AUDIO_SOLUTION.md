# Решение для больших аудио файлов через MinIO

## 💡 Концепция

Обход ограничений Telegram Bot API (20 МБ) через альтернативные методы загрузки и обработки больших файлов.

## 🔧 Техническое решение

### 1. Получение прямой ссылки на файл
```python
# Telegram предоставляет прямые ссылки на файлы через веб-интерфейс
# Формат: https://api.telegram.org/file/bot<TOKEN>/<file_path>
# Но file_path недоступен для файлов > 20 МБ через Bot API
```

### 2. Альтернативный подход - веб-интерфейс
```python
async def handle_large_audio_via_web(file_id: str, user_id: int):
    """
    Обработка больших файлов через веб-интерфейс
    """
    # 1. Создаем временную ссылку для пользователя
    upload_token = generate_upload_token(user_id, file_id)
    
    # 2. Отправляем пользователю ссылку на веб-страницу
    web_url = f"https://aibots.kz/upload?token={upload_token}"
    
    # 3. Пользователь загружает файл через веб-интерфейс
    # 4. Файл сохраняется в MinIO
    # 5. Запускается обработка
```

### 3. Архитектура решения
```
Пользователь отправляет файл > 20 МБ
          ↓
Бот определяет, что файл большой
          ↓
Генерируется уникальная ссылка для загрузки
          ↓
Пользователь переходит на веб-страницу
          ↓
Файл загружается напрямую в MinIO
          ↓
Запускается обработка через Whisper
          ↓
Результат отправляется в Telegram
```

## 🛠️ Реализация

### 1. Веб-интерфейс для загрузки
```html
<!-- upload.html -->
<form id="audioUpload" enctype="multipart/form-data">
    <input type="file" name="audio" accept="audio/*" required>
    <button type="submit">Загрузить для обработки</button>
</form>
```

### 2. API endpoint для загрузки
```python
@app.post("/api/v1/upload/audio")
async def upload_large_audio(
    file: UploadFile,
    token: str,
    storage: StorageService = Depends(get_storage)
):
    # Валидация токена
    user_id = validate_upload_token(token)
    
    # Сохранение в MinIO
    file_key = f"audio/{user_id}/{uuid4()}.{file.filename.split('.')[-1]}"
    await storage.upload_file("audio", file_key, file.file)
    
    # Запуск обработки в фоне
    await queue_audio_processing(user_id, file_key)
    
    return {"status": "uploaded", "message": "Файл загружен, обработка начата"}
```

### 3. Обработчик больших файлов в боте
```python
async def handle_large_audio_file(message: Message, file_size: int):
    """Обработка больших аудио файлов"""
    
    # Генерируем токен для загрузки
    upload_token = generate_upload_token(
        user_id=message.from_user.id,
        file_id=message.audio.file_id if message.audio else message.voice.file_id,
        expires_in=3600  # 1 час
    )
    
    # Создаем ссылку для загрузки
    upload_url = f"https://aibots.kz/upload?token={upload_token}"
    
    # Отправляем пользователю инструкции
    await message.reply(
        f"📁 **Большой файл обнаружен**\n\n"
        f"📊 Размер: {file_size / (1024*1024):.1f} МБ\n"
        f"🚫 Лимит Telegram: 20 МБ\n\n"
        f"💡 **Решение:**\n"
        f"Перейдите по ссылке для загрузки файла:\n"
        f"🔗 {upload_url}\n\n"
        f"⏱️ Ссылка действительна 1 час\n"
        f"📱 После загрузки вы получите уведомление",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
```

## 🔄 Workflow для пользователя

### Сценарий использования:
1. **Пользователь отправляет файл 60 МБ**
2. **Бот отвечает:** "Файл слишком большой, перейдите по ссылке"
3. **Пользователь переходит на веб-страницу**
4. **Загружает тот же файл через браузер**
5. **Получает уведомление:** "Файл загружен, обработка начата"
6. **Через несколько минут:** "Транскрипция готова!" + файл

## 📋 Преимущества решения

### ✅ Плюсы:
- Обход ограничений Telegram Bot API
- Поддержка файлов до 2 ГБ (лимит веб-интерфейса)
- Прямая загрузка в MinIO
- Безопасность через временные токены

### ⚠️ Минусы:
- Дополнительный шаг для пользователя
- Нужен веб-интерфейс
- Сложность реализации

## 🚀 План реализации

### Этап 1: Базовая инфраструктура
- [ ] Веб-страница для загрузки файлов
- [ ] API endpoint для приема файлов
- [ ] Система токенов для безопасности

### Этап 2: Интеграция с ботом
- [ ] Обработчик больших файлов
- [ ] Генерация ссылок для загрузки
- [ ] Уведомления о статусе обработки

### Этап 3: Оптимизация
- [ ] Прогресс-бар загрузки
- [ ] Автоматическое сжатие на сервере
- [ ] Поддержка drag&drop

## 💻 Альтернативные решения

### 1. Интеграция с облачными сервисами
```python
# Поддержка ссылок на Google Drive, Dropbox, etc.
if message.text and is_cloud_link(message.text):
    await download_from_cloud(message.text)
```

### 2. Telegram Web App
```python
# Использование Telegram Mini Apps для загрузки
web_app_url = "https://aibots.kz/webapp/upload"
keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton("📁 Загрузить файл", web_app=WebApp(url=web_app_url))
]])
```

## 🎯 Рекомендация

**Для файла 60 МБ пользователя:**
1. **Краткосрочно:** Сжать файл до < 20 МБ
2. **Долгосрочно:** Реализовать веб-интерфейс для больших файлов

**Приоритет реализации:** Средний (после основных функций)
**Сложность:** Высокая
**Время разработки:** 1-2 недели 