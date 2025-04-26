# Aisha Bot — Telegram-бот для протоколов и транскриптов

## Описание

Aisha Bot — это Telegram-бот для автоматической расшифровки аудио, обработки текстовых транскриптов и генерации деловых документов (протоколы, MoM, ToDo, сводки) с помощью GPT и шаблонов Word.

## Основные функции

- Приём аудиофайлов и голосовых сообщений, автоматическая расшифровка через Whisper/OpenAI
- Приём текстовых файлов (.txt) с транскриптами
- Автоматическая валидация файлов при загрузке:
  - Аудиофайл должен быть в одном из поддерживаемых форматов (mp3, wav, ogg, m4a, flac, aac, wma, opus)
  - Текстовый транскрипт должен быть не менее 1000 символов, без бинарных и нечитабельных символов
- Меню выбора формата результата: 
  - Полный официальный транскрипт
  - Сводка на 1 страницу
  - MoM (Minutes of Meeting)
  - ToDo-план с чеклистами
  - Протокол заседания (Word)
- Генерация Word-документов по шаблону (папка `templates/`)
- Возможность повторить генерацию протокола без повторной загрузки файла
- Централизованное логирование действий и ошибок (директория `logs/`)
- Удобный UX: кнопки "Назад", "Главное меню", информативные сообщения

## Быстрый старт

1. Клонируйте репозиторий и установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Создайте файл `.env` в корне проекта и укажите:
   ```env
   TELEGRAM_TOKEN=... # токен вашего бота
   OPENAI_API_KEY=... # ключ OpenAI
   LOG_LEVEL=INFO     # уровень логирования (DEBUG, INFO, WARNING, ERROR)
   ```
3. (Опционально) Поместите шаблон Word для протокола в папку `templates/protocol_template.docx`.
4. Запустите бота:
   ```bash
   python -m frontend_bot.bot
   ```

## Настройка логирования

- Все логи пишутся в папку `logs/`.
- Уровень логирования задаётся переменной окружения `LOG_LEVEL` (`INFO` по умолчанию).
- Для каждого сервиса создаётся отдельный лог-файл (например, `transcribe.log`).

## Описание команд и UX

- После загрузки аудио или .txt-файла появляется меню выбора формата обработки.
- После ошибки доступны кнопки "Повторить" и "Главное меню".
- После успешной генерации документа — подтверждение и возврат в меню.
- Для протокола Word поддерживается повторная генерация без повторной загрузки файла.

## Новые возможности и улучшения

- Централизованный логгер с настройкой уровня логирования
- Поддержка шаблонов Word для протоколов (папка `templates/`)
- Улучшенный UX: дополнительные кнопки, информативные сообщения, возврат в меню
- Обработка как аудио, так и текстовых транскриптов
- Возможность повторной генерации протокола

## Структура проекта

- `frontend_bot/handlers/` — обработчики Telegram-сообщений
- `frontend_bot/services/` — сервисы GPT, генерация Word, интеграции
- `frontend_bot/utils/logger.py` — централизованный логгер
- `templates/` — шаблоны Word для документов
- `logs/` — директория для логов

---

**Aisha Bot** — ваш помощник для автоматизации деловых встреч и протоколирования!

```
aisha_bot/
├── frontend-bot/                 # Telegram bot (юзерский интерфейс)
│   ├── main.py                   # Точка входа: запуск polling через asyncio
│   ├── bot.py                    # Инициализация и регистрация хендлеров
│   ├── handlers/                 # Обработка команд / фич (wedding, talking и др.)
│   ├── services/                 # REST-клиенты (к backend-api)
│   ├── keyboards/                # Inline и ReplyMarkup
│   ├── storage/                  # Локальные файлы (игнорируется git)
│   ├── config.py                 # Токены, API_URL
│   ├── requirements.txt          # Зависимости
│   ├── .env                      # Секреты и токены (игнорируется git)
│   └── .gitignore                # Исключения для git
│
├── backend-api/                  # REST API для генерации видео, TTS и прочего
│   ├── app/
│   │   ├── main.py               # FastAPI
│   │   ├── routers/              # /animate, /tts, /health
│   │   ├── workers/              # async задачи (например, Celery воркеры)
│   │   ├── services/             # D-ID, OpenAI, FAISS и т.п.
│   │   └── models.py             # Pydantic-схемы
│   ├── Dockerfile
│   └── requirements.txt
│
├── database/                     # Скрипты и миграции для PostgreSQL
│   └── init.sql
│
├── shared/                       # Общие модули (например, обработка изображений)
│   └── image_utils.py
│
├── docker-compose.yml            # Локальная сборка всего проекта
└── README.md                     # Документация
```

- Все секреты и токены хранятся в `.env` (не коммитить!).
- Вся логика хендлеров — в папке `handlers/`.
- Для клавиатур используйте папку `keyboards/`.
- Для интеграций с внешними сервисами — папку `services/`.
- Для запуска Telegram-бота используйте `python main.py` из папки `frontend-bot/`.
- Для запуска backend используйте FastAPI-приложение из `backend-api/app/main.py`.


sudo useradd -r -s /usr/sbin/nologin aisha
sudo usermod -aG docker aisha

sudo chown -R aisha:aisha /opt/aisha_bot
sudo chmod -R 750 /opt/aisha_bot

# модуль транскрибации аудио:

sudo apt update
sudo apt install ffmpeg

TODO история обработок пока что хранится в JSON файле прям в проекте. В будущем переносим в БД 




docker pull soulteary/docker-gfpgan:latest
wget -O /opt/aisha_bot/models/GFPGAN/weights/GFPGANv1.4.pth https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth

sudo docker run -d --rm -p 7860:7860 \
  -v /opt/aisha_bot/models/GFPGAN/weights/GFPGANv1.4.pth:/GFPGAN.pth \
  -v /opt/aisha_bot/models/GFPGAN/weights/:/workspace \
  -w /workspace \
  soulteary/docker-gfpgan:latest

  sudo docker ps # проверить, что контейнер работает
  sudo docker logs <container_id> # посмотреть логи контейнера
  sudo docker logs $(sudo docker ps -q) # если контейнер только один
  sudo docker stop <container_id> # остановить контейнер

  37.151.92.11

TODO дать пользователю выбор (upscale, формат, только центральное лицо, авто/ручной режим)?