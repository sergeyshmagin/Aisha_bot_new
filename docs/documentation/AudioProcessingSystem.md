# Система обработки аудио

**Модуль:** `app/services/audio_processing/`

## Описание

Модульная система для обработки аудио файлов, включающая конвертацию, распознавание речи, нормализацию и хранение. Система построена на принципах SOLID и использует dependency injection.

## Архитектура

```
AudioProcessingSystem
├── service.py              # Основной сервис-оркестратор
├── converter.py            # Конвертация форматов (FFmpeg/pydub)
├── processor.py            # Обработка аудио (нормализация, разбиение)
├── recognizer.py           # Распознавание речи (Whisper API)
├── storage.py              # Локальное хранение файлов
└── types.py                # Интерфейсы и типы данных
```

## Основные компоненты

### AudioService
**Файл:** `service.py`

Главный сервис-оркестратор, координирующий работу всех компонентов.

**Основные методы:**
- `process_audio()` - Полная обработка аудио с транскрибацией
- `transcribe_file()` - Транскрибация существующего файла
- `cleanup()` - Очистка старых файлов

**Пример использования:**
```python
service = AudioService(converter, recognizer, processor, storage)
result = await service.process_audio(audio_data, language="ru")
```

### PydubAudioConverter
**Файл:** `converter.py`

Конвертер аудио форматов с поддержкой FFmpeg и pydub.

**Возможности:**
- Конвертация в MP3 через FFmpeg или pydub
- Автоматическое определение формата по magic bytes
- Получение метаданных аудио файлов
- Поддержка форматов: MP3, WAV, M4A, OGG, FLAC, AAC

**Методы:**
- `convert_to_mp3()` - Конвертация в MP3
- `detect_format()` - Определение формата файла
- `get_metadata()` - Извлечение метаданных

### AudioProcessor
**Файл:** `processor.py`

Обработчик аудио для нормализации и разбиения на части.

**Функции:**
- Разбиение по тишине (pydub/FFmpeg)
- Нормализация громкости
- Удаление тишины с краев
- Валидация качества аудио

**Методы:**
- `split_audio()` - Разбиение на части по паузам
- `normalize_audio()` - Нормализация громкости
- `remove_silence()` - Удаление тишины

### WhisperRecognizer
**Файл:** `recognizer.py`

Распознаватель речи на основе OpenAI Whisper API.

**Особенности:**
- Поддержка больших файлов (автоматическое разбиение)
- Retry механизм для надежности
- Обработка rate limiting
- Мультиязычная поддержка

**Методы:**
- `transcribe()` - Основная транскрибация
- `transcribe_chunk()` - Транскрибация части файла

### LocalAudioStorage
**Файл:** `storage.py`

Локальное хранилище аудио файлов с управлением жизненным циклом.

**Функции:**
- Сохранение/загрузка файлов
- Автоматическая очистка старых файлов
- UUID-based именование
- Безопасное удаление

## Типы данных

### TranscribeResult
```python
@dataclass
class TranscribeResult:
    success: bool
    text: str = ""
    error: Optional[str] = None
    metadata: Optional[AudioMetadata] = None
```

### AudioMetadata
```python
@dataclass
class AudioMetadata:
    duration: float
    format: str
    sample_rate: int
    channels: int
    bitrate: int
    created_at: datetime
```

## Конфигурация

### Переменные окружения
- `FFMPEG_PATH` - Путь к FFmpeg
- `OPENAI_API_KEY` - API ключ OpenAI
- `AUDIO_STORAGE_PATH` - Путь для хранения файлов
- `MAX_AUDIO_SIZE` - Максимальный размер файла
- `AUDIO_FORMATS` - Поддерживаемые форматы

### Настройки обработки
- Минимальная длина тишины: 700ms
- Порог тишины: -30dB
- Максимальная длина для Whisper: 300 секунд
- Retry попытки: 3

## Обработка ошибок

Все компоненты используют `AudioProcessingError` из модульной системы исключений:

```python
from app.core.exceptions.audio_exceptions import AudioProcessingError
```

**Типы ошибок:**
- Ошибки конвертации
- Ошибки транскрибации
- Ошибки хранения
- Ошибки валидации

## Использование

### Базовый пример
```python
from app.services.audio_processing.service import AudioService
from app.services.audio_processing.converter import PydubAudioConverter
from app.services.audio_processing.recognizer import WhisperRecognizer
from app.services.audio_processing.processor import AudioProcessor
from app.services.audio_processing.storage import LocalAudioStorage

# Инициализация компонентов
converter = PydubAudioConverter()
recognizer = WhisperRecognizer()
processor = AudioProcessor()
storage = LocalAudioStorage()

# Создание сервиса
service = AudioService(converter, recognizer, processor, storage)

# Обработка аудио
result = await service.process_audio(audio_bytes, language="ru")
if result.success:
    print(f"Транскрипт: {result.text}")
```

### Продвинутое использование
```python
# Обработка с настройками
result = await service.process_audio(
    audio_data=audio_bytes,
    language="ru",
    save_original=True,
    normalize=True,
    remove_silence=True
)

# Транскрибация существующего файла
result = await service.transcribe_file(
    filename="audio.mp3",
    language="en",
    normalize=False
)

# Очистка старых файлов
await service.cleanup(max_age_days=7)
```

## Зависимости

- `pydub` - Обработка аудио
- `aiohttp` - HTTP клиент для API
- `aiofiles` - Асинхронная работа с файлами
- `ffmpeg` - Конвертация форматов (внешняя зависимость)

## Тестирование

Система покрыта unit-тестами с использованием pytest-asyncio:

```bash
pytest tests/services/test_audio_processing.py -v
```

## Статус

✅ **Активный** - Используется для обработки голосовых сообщений в боте

## Планы развития

- [ ] Поддержка streaming обработки
- [ ] Интеграция с другими STT сервисами
- [ ] Кэширование результатов транскрибации
- [ ] Метрики производительности 