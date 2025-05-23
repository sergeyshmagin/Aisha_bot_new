# Инвентаризация кода проекта Aisha v2

*Дата: 22.05.2025*

## Общая структура проекта

```
aisha_v2/
├── alembic/            # Миграции базы данных
├── app/                # Основной код приложения
│   ├── core/           # Ядро приложения (конфиги, константы, исключения)
│   ├── database/       # Модели и репозитории
│   ├── handlers/       # Обработчики команд бота
│   ├── keyboards/      # Клавиатуры для бота
│   ├── prompts/        # Промпты для GPT
│   ├── services/       # Сервисы (бизнес-логика)
│   ├── texts/          # Тексты для пользовательского интерфейса
│   └── utils/          # Утилиты
├── docs/               # Документация
├── scripts/            # Вспомогательные скрипты
├── storage/            # Хранилище файлов
└── tests/              # Тесты
```

## Модели данных

### Основные модели
- **User**: Модель пользователя
  - Связи: avatars, avatar_photos, balance, state, transcripts, profile
  - Поля: telegram_id, first_name, last_name, username, language_code, timezone, is_premium, is_bot, is_blocked

- **UserTranscript**: Модель транскрипта пользователя
  - Связи: user
  - Поля: user_id, audio_key, transcript_key, transcript_metadata, created_at, updated_at

- **UserTranscriptCache**: Кэш последнего транскрипта пользователя
  - Связи: user
  - Поля: user_id, path, created_at

- **UserBalance**: Баланс пользователя
  - Связи: user
  - Поля: user_id, coins, created_at, updated_at

- **UserState**: Состояние пользователя
  - Связи: user
  - Поля: user_id, state_data, created_at, updated_at

- **Avatar**: Модель аватара
  - Связи: user, photos
  - Поля: user_id, name, gender, status, is_draft, avatar_data, photo_key, preview_key

- **AvatarPhoto**: Фотография для аватара
  - Связи: avatar, user
  - Поля: avatar_id, minio_key, order, user_id, photo_metadata, photo_hash

- **UserProfile**: Модель профиля пользователя
  - Связи: user
  - Поля: user_id, avatar_path, bio, created_at, updated_at

## Репозитории

### Основные репозитории
- **BaseRepository**: Базовый репозиторий с общей функциональностью CRUD
- **TranscriptRepository**: Репозиторий для работы с транскриптами
  - Методы: get_user_transcripts, get_transcript_by_id, get_transcript_by_id_only, count_user_transcripts
- **UserRepository**: Репозиторий для работы с пользователями
- **AvatarRepository**: Репозиторий для работы с аватарами
- **BalanceRepository**: Репозиторий для работы с балансом пользователей
- **StateRepository**: Репозиторий для работы с состояниями пользователей

## Сервисы

### Сервисы транскрибации
- **TranscriptService**: Сервис для работы с транскриптами
  - Методы: save_transcript, get_transcript, get_user_transcripts, list_transcripts, delete_transcript, get_transcript_content

- **AudioProcessingService**: Сервис для обработки аудио
  - Модули: 
    - `converter.py`: Конвертация аудио в разные форматы
    - `factory.py`: Фабрика для создания компонентов обработки аудио
    - `processor.py`: Обработка аудио (сегментация, нормализация)
    - `recognizer.py`: Распознавание аудио через Whisper API
    - `service.py`: Основной сервис обработки аудио
    - `storage.py`: Хранение аудиофайлов
    - `types.py`: Типы данных для обработки аудио

- **TextProcessingService**: Сервис для обработки текста
  - Функциональность: 
    - Генерация кратких содержаний через GPT
    - Создание списков задач через GPT
    - Генерация протоколов встреч

### Другие сервисы
- **BackendService**: Сервис для работы с бэкендом
- **AvatarDBService**: Сервис для работы с базой данных аватаров
- **UserService**: Сервис для работы с пользователями
- **StorageService**: Сервис для работы с файловым хранилищем (MinIO)

## Обработчики команд

### Обработчики транскрибации
- **TranscriptBaseHandler**: Базовый обработчик для транскрибации
- **TranscriptMainHandler**: Главный обработчик команд транскрибации
- **TranscriptManagementHandler**: Обработчик управления транскриптами
- **TranscriptProcessingHandler**: Обработчик обработки транскриптов
- **TranscriptViewHandler**: Обработчик просмотра транскриптов

### Другие обработчики
- **AudioHandler**: Обработчик аудио
- **AvatarHandler**: Обработчик аватаров
- **BaseHandler**: Базовый обработчик
- **BusinessHandler**: Обработчик бизнес-логики
- **FallbackHandler**: Обработчик для неизвестных команд
- **GalleryHandler**: Обработчик галереи
- **MainMenuHandler**: Обработчик главного меню
- **MenuHandler**: Обработчик меню
- **StateHandler**: Обработчик состояний

## Клавиатуры
- Клавиатуры для работы с транскриптами
- Клавиатуры для главного меню
- Клавиатуры для различных функций бота

## Конфигурация и константы

### Конфигурация
- **config.py**: Настройки проекта
  - Настройки подключения к базе данных
  - Настройки Telegram бота
  - Настройки MinIO
  - Настройки Redis
  - Настройки Whisper API (WHISPER_MODEL: "whisper-1", WHISPER_LANGUAGE: "ru")

### Константы
- **constants.py**: Константы проекта
  - Максимальный размер файла (MAX_FILE_SIZE = 100 * 1024 * 1024, 100 МБ)
  - Максимальная длительность аудио (MAX_AUDIO_DURATION = 60 * 60, 60 минут)
  - Максимальное количество транскриптов на пользователя (MAX_TRANSCRIPTS_PER_USER = 50)

### Ресурсы
- **resources.py**: Префиксы ключей для кэширования
  - "transcript": "cache:v2:transcript:" - для кэширования транскриптов
  - "audio": "cache:v2:audio:" - для кэширования аудио

## Промпты и тексты

### Промпты
- Промпты для GPT для работы с транскриптами
- Структура: `/app/prompts/transcribe/`

### Тексты
- Тексты для пользовательского интерфейса
- Структура: `/app/texts/transcribe/`

## Интеграции с внешними сервисами

### База данных
- PostgreSQL: Хранение метаданных (пользователи, транскрипты, и т.д.)

### Кэширование
- Redis: Кэширование данных и хранение состояний FSM
  - Хост: 192.168.0.3
  - Порт: 6379
  - БД: 0

### Хранение файлов
- MinIO: Хранение аудио файлов и текстовых транскриптов

### API сервисы
- OpenAI Whisper API: Транскрибация аудио
- OpenAI GPT API: Обработка текста и генерация

## Обработка ошибок
- **exceptions.py**: Обработка исключений
  - AudioProcessingError: Ошибки при обработке аудио
  - Другие специализированные исключения

## Обнаруженные проблемы и технический долг

### Проблемы
1. **Зависимость от pydub**: При отсутствии pydub функциональность обработки аудио ограничена
   ```python
   PYDUB_AVAILABLE = False
   try:
       from pydub import AudioSegment
       PYDUB_AVAILABLE = True
   except ImportError:
       logging.warning("pydub не установлен, функции обработки аудио будут ограничены")
       AudioSegment = None
   ```

2. **Проблема с полем 'metadata'**: Поле было переименовано в 'transcript_metadata' из-за конфликта с SQLAlchemy Declarative API
   ```
   sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
   ```

### Технический долг
1. Отсутствие полного покрытия тестами
2. Необходимость рефакторинга обработчиков для лучшего разделения ответственности
3. Потребность в оптимизации работы с большими аудиофайлами
4. Требуется внедрение пагинации в списке транскриптов

## Следующие шаги
1. **Тестирование**: Создание комплексных тестов для всей функциональности транскрибации
2. **Рефакторинг**: Улучшение структуры кода и разделение ответственности
3. **Производительность**: Оптимизация работы с большими файлами
4. **UX**: Улучшение пользовательского интерфейса и добавление новых функций
