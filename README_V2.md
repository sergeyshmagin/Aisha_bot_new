# Telegram AI Bot — Highload Edition

## Описание

Асинхронный Telegram-бот для обработки аудио- и фотофайлов с поддержкой транскрипции, улучшения фото (GFPGAN), истории файлов и гибкой архитектурой для высоких нагрузок.

- **Асинхронная обработка** всех файловых операций (`aiofiles`)
- **Асинхронный запуск внешних процессов** (`ffmpeg`, `ffprobe`) через `asyncio.create_subprocess_exec`
- **Гибкое хранение состояния пользователя** через state_manager (готово к миграции на Redis)
- **Масштабируемая архитектура**: легко добавить новые режимы и обработчики
- **PEP8, docstring, чистый код**

## Требования

- Python 3.9+
- ffmpeg (установлен в системе)
- [aiofiles](https://pypi.org/project/aiofiles/)
- [telebot](https://pypi.org/project/pyTelegramBotAPI/) (или aiogram, если используется)
- aiohttp
- dotenv
- (опционально) Redis для state_manager в будущем

## Быстрый старт

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Установите ffmpeg (Linux: `sudo apt install ffmpeg`, Windows: [скачать](https://ffmpeg.org/download.html))
3. Создайте `.env` с токеном Telegram и настройками:
   ```env
   TELEGRAM_TOKEN=...  # ваш токен
   OPENAI_API_KEY=...  # для Whisper
   STORAGE_DIR=storage
   ```
4. Запустите бота:
   ```bash
   python -m frontend_bot.main
   ```

## Основные возможности

- **Транскрипция аудио** (mp3, ogg, wav и др.) через OpenAI Whisper
- **Обработка текстовых транскриптов (.txt)**
- **Улучшение фото через GFPGAN** (Docker backend)
- **История файлов пользователя**
- **Гибкое меню и режимы работы** (state_manager)
- **Асинхронная обработка файлов и процессов**

## Архитектурные особенности

- Все I/O-операции (чтение/запись файлов) — асинхронные
- Все вызовы ffmpeg/ffprobe — асинхронные, не блокируют event loop
- Состояния пользователя (режимы) централизованы через state_manager (dict, готово к Redis)
- Легко масштабируется на несколько воркеров/серверов
- Готов к highload: не блокирует event loop даже при массовой обработке

## Рекомендации для highload

- Для продакшена используйте Redis для state_manager (заменить реализацию в `services/state_manager.py`)
- Запускайте несколько воркеров через supervisor/systemd
- Мониторьте нагрузку на ffmpeg и I/O
- Используйте отдельный backend для GFPGAN (Docker)

## Пример расширения

Добавить новый режим (например, "Озвучить текст"):
1. Добавьте кнопку в клавиатуру
2. В state_manager добавьте новый режим
3. Реализуйте обработчик для нужного типа файла/текста

## Контакты и поддержка

- Вопросы и баги — через Issues на GitHub
- Поддержка и доработка — по запросу 

@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message):
    print("DEBUG: text_instruction called")
    ... 