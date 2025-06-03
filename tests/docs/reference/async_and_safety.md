# Async Python и безопасность - лучшие практики

## 🚀 Асинхронное программирование

### 1. Основные принципы

#### 1.1 Всегда async/await
```python
# ✅ Правильно
async def process_audio(file_data: bytes) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/...", data=file_data)
        return response.text

# ❌ Неправильно
def process_audio(file_data: bytes) -> str:
    response = requests.post("https://api.openai.com/...", data=file_data)
    return response.text
```

#### 1.2 Контекстные менеджеры для ресурсов
```python
# ✅ Правильно
async def get_transcript(user_id: str, transcript_id: str):
    async with get_session() as session:
        transcript_service = get_transcript_service(session)
        result = await transcript_service.get_transcript(user_id, transcript_id)
        return result

# ❌ Неправильно
async def get_transcript(user_id: str, transcript_id: str):
    session = get_session()  # Ресурс не освобождается автоматически
    transcript_service = get_transcript_service(session)
    result = await transcript_service.get_transcript(user_id, transcript_id)
    return result
```

#### 1.3 Правильная обработка исключений в async
```python
# ✅ Правильно
async def safe_process():
    try:
        async with get_session() as session:
            result = await some_async_operation(session)
            return result
    except DatabaseError as e:
        logger.error(f"[DB] Ошибка БД: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.exception(f"[PROCESS] Неизвестная ошибка: {e}")
        raise

# ❌ Неправильно
async def unsafe_process():
    session = get_session()
    try:
        result = await some_async_operation(session)
        return result
    except Exception as e:
        # Сессия может не закрыться при ошибке
        logger.error(f"Ошибка: {e}")
```

### 2. Работа с файлами

#### 2.1 Асинхронное чтение/запись
```python
# ✅ Правильно
import aiofiles

async def read_file(file_path: str) -> str:
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        return content

async def write_file(file_path: str, content: str):
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(content)

# ❌ Неправильно в async коде
def read_file_sync(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:  # Блокирующая операция
        return f.read()
```

#### 2.2 Работа с временными файлами
```python
# ✅ Правильно
import aiofiles.tempfile

async def process_temp_file(data: bytes):
    async with aiofiles.tempfile.NamedTemporaryFile(mode='wb', delete=True) as tmp_file:
        await tmp_file.write(data)
        await tmp_file.flush()
        # Файл автоматически удалится
        return await process_file(tmp_file.name)
```

### 3. Сетевые запросы

#### 3.1 HTTP клиенты
```python
# ✅ Правильно
import httpx

async def make_api_request(url: str, data: dict):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()

# ❌ Неправильно в async коде
import requests

def make_api_request_sync(url: str, data: dict):
    response = requests.post(url, json=data)  # Блокирующий запрос
    return response.json()
```

#### 3.2 Параллельные запросы
```python
# ✅ Правильно
import asyncio

async def parallel_requests(urls: List[str]):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

### 4. База данных

#### 4.1 SQLAlchemy async сессии
```python
# ✅ Правильно
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_transcripts(session: AsyncSession, user_id: str):
    stmt = select(UserTranscript).where(UserTranscript.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()

# ❌ Неправильно
def get_user_transcripts_sync(session, user_id: str):
    stmt = select(UserTranscript).where(UserTranscript.user_id == user_id)
    result = session.execute(stmt)  # Синхронный вызов в async коде
    return result.scalars().all()
```

#### 4.2 Транзакции
```python
# ✅ Правильно
async def create_transcript_with_metadata(session: AsyncSession, transcript_data: dict):
    async with session.begin():  # Автоматический rollback при ошибке
        transcript = UserTranscript(**transcript_data)
        session.add(transcript)
        await session.flush()  # Получаем ID
        
        metadata = TranscriptMetadata(transcript_id=transcript.id, ...)
        session.add(metadata)
        # Commit происходит автоматически
        return transcript
```

### 5. Обработка ошибок

#### 5.1 Специфичные исключения
```python
# ✅ Правильно
class TranscriptNotFoundError(Exception):
    pass

class AudioProcessingError(Exception):
    pass

async def process_transcript(user_id: str, transcript_id: str):
    try:
        transcript = await get_transcript(user_id, transcript_id)
        if not transcript:
            raise TranscriptNotFoundError(f"Транскрипт {transcript_id} не найден")
        
        result = await process_audio(transcript.audio_data)
        return result
    except TranscriptNotFoundError:
        raise  # Пробрасываем дальше
    except AudioProcessingError as e:
        logger.error(f"[AUDIO] Ошибка обработки: {e}")
        raise
    except Exception as e:
        logger.exception(f"[TRANSCRIPT] Неизвестная ошибка: {e}")
        raise AudioProcessingError("Ошибка обработки транскрипта")
```

#### 5.2 Graceful degradation
```python
# ✅ Правильно
async def get_transcript_with_fallback(user_id: str, transcript_id: str):
    try:
        # Пытаемся получить из кэша
        cached = await get_from_cache(transcript_id)
        if cached:
            return cached
    except CacheError:
        logger.warning("[CACHE] Кэш недоступен, используем БД")
    
    try:
        # Fallback на БД
        return await get_from_database(user_id, transcript_id)
    except DatabaseError as e:
        logger.error(f"[DB] БД недоступна: {e}")
        raise ServiceUnavailableError("Сервис временно недоступен")
```

## 🔒 Безопасность

### 1. Управление секретами

#### 1.1 Переменные окружения
```python
# ✅ Правильно
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., min_length=40)
    openai_api_key: str = Field(..., min_length=40)
    database_url: str = Field(..., min_length=10)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# ❌ Неправильно
TELEGRAM_BOT_TOKEN = "1234567890:ABCDEF..."  # Хардкод в коде
```

#### 1.2 Логирование без секретов
```python
# ✅ Правильно
def safe_log_request(url: str, headers: dict, data: dict):
    safe_headers = {k: "***" if "token" in k.lower() or "key" in k.lower() 
                   else v for k, v in headers.items()}
    safe_data = {k: "***" if "password" in k.lower() else v 
                for k, v in data.items()}
    logger.info(f"[API] Request to {url}, headers={safe_headers}, data={safe_data}")

# ❌ Неправильно
def unsafe_log_request(url: str, headers: dict, data: dict):
    logger.info(f"[API] Request to {url}, headers={headers}, data={data}")  # Может логировать токены
```

### 2. Валидация данных

#### 2.1 Pydantic модели
```python
# ✅ Правильно
from pydantic import BaseModel, Field, validator

class TranscriptRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    audio_data: bytes = Field(..., min_length=1, max_length=50*1024*1024)  # 50MB max
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.isalnum():
            raise ValueError('user_id должен содержать только буквы и цифры')
        return v

# ❌ Неправильно
def process_transcript(user_id, audio_data):
    # Нет валидации входных данных
    return do_something(user_id, audio_data)
```

#### 2.2 SQL инъекции
```python
# ✅ Правильно
async def get_user_by_id(session: AsyncSession, user_id: str):
    stmt = select(User).where(User.id == user_id)  # Параметризованный запрос
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# ❌ Неправильно
async def get_user_by_id_unsafe(session: AsyncSession, user_id: str):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL инъекция
    result = await session.execute(text(query))
    return result.fetchone()
```

### 3. Контроль доступа

#### 3.1 Проверка прав пользователя
```python
# ✅ Правильно
async def get_transcript(user_id: str, transcript_id: str):
    transcript = await transcript_repo.get_by_id(transcript_id)
    if not transcript:
        raise TranscriptNotFoundError()
    
    if transcript.user_id != user_id:
        raise PermissionDeniedError("Нет доступа к данному транскрипту")
    
    return transcript

# ❌ Неправильно
async def get_transcript_unsafe(transcript_id: str):
    # Нет проверки принадлежности пользователю
    return await transcript_repo.get_by_id(transcript_id)
```

#### 3.2 Rate limiting
```python
# ✅ Правильно
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.window:
            user_requests.pop(0)
        
        if len(user_requests) >= self.max_requests:
            return False
        
        user_requests.append(now)
        return True

rate_limiter = RateLimiter()

async def process_request(user_id: str, data: dict):
    if not rate_limiter.is_allowed(user_id):
        raise RateLimitExceededError("Слишком много запросов")
    
    return await do_processing(data)
```

## 🧪 Тестирование async кода

### 1. pytest-asyncio
```python
# ✅ Правильно
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def async_session():
    async with get_test_session() as session:
        yield session

@pytest.mark.asyncio
async def test_transcript_creation(async_session):
    transcript = await create_transcript(async_session, test_data)
    assert transcript.id is not None
    assert transcript.user_id == test_data['user_id']
```

### 2. Мокирование async функций
```python
# ✅ Правильно
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_audio_processing():
    with patch('app.services.openai.process_audio', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "test transcript"
        
        result = await audio_service.process(test_audio_data)
        
        assert result == "test transcript"
        mock_process.assert_called_once_with(test_audio_data)
```

## 📊 Мониторинг и отладка

### 1. Структурированное логирование
```python
# ✅ Правильно
import structlog

logger = structlog.get_logger()

async def process_transcript(user_id: str, transcript_id: str):
    log = logger.bind(user_id=user_id, transcript_id=transcript_id)
    
    log.info("[TRANSCRIPT] Начало обработки")
    try:
        result = await do_processing()
        log.info("[TRANSCRIPT] Обработка завершена", duration=duration)
        return result
    except Exception as e:
        log.error("[TRANSCRIPT] Ошибка обработки", error=str(e))
        raise
```

### 2. Timing и метрики
```python
# ✅ Правильно
import time
from functools import wraps

def timing(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"[TIMING] {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"[TIMING] {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

@timing
async def process_audio(audio_data: bytes):
    return await heavy_processing(audio_data)
```

---

**См. также:**
- `docs/architecture.md` - общая архитектура проекта
- `docs/best_practices.md` - общие лучшие практики 