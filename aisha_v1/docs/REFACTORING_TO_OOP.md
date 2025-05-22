# План перехода на ООП

## 1. Общая структура классов

### 1.1. Backend API Layer
```python
class BackendAPIClient:
    """Клиент для взаимодействия с Backend API"""
    def __init__(self, config: BackendConfig):
        self.config = config
        self.session: aiohttp.ClientSession

    async def enhance_photo(self, photo_data: bytes) -> bytes:
        """Улучшение фото через GFPGAN"""

    async def train_avatar(self, user_id: int, avatar_id: str, photos: List[bytes]) -> str:
        """Запуск тренировки аватара"""

    async def check_training_status(self, training_id: str) -> Dict:
        """Проверка статуса тренировки"""

class BackendService(BaseService):
    """Сервис для работы с Backend API"""
    def __init__(self, api_client: BackendAPIClient):
        self.api_client = api_client

    async def process_avatar_training(self, user_id: int, avatar_id: str) -> str:
        """Обработка тренировки аватара"""

    async def enhance_user_photo(self, photo_data: bytes) -> bytes:
        """Улучшение фото пользователя"""

class BackendConfig:
    """Конфигурация Backend API"""
    def __init__(self):
        self.api_url: str
        self.api_key: str
        self.timeout: int
```

### 1.1. Core (Ядро системы)
```python
class AishaBot:
    """Основной класс бота, управляющий всеми компонентами"""
    def __init__(self):
        self.config = BotConfig()
        self.db = DatabaseManager()
        self.storage = StorageManager()
        self.services = ServiceContainer()
        self.handlers = HandlerContainer()
        
    async def start(self):
        """Запуск бота и всех компонентов"""
        
    async def stop(self):
        """Graceful shutdown"""

class BotConfig:
    """Конфигурация бота"""
    def __init__(self):
        self.telegram_token: str
        self.database_url: str
        self.minio_config: MinioConfig
        # ...

class ServiceContainer:
    """Контейнер для всех сервисов"""
    def __init__(self):
        self.user_service: UserService
        self.avatar_service: AvatarService
        self.transcript_service: TranscriptService
        self.backend_service: BackendService
        # ...

class HandlerContainer:
    """Контейнер для всех обработчиков"""
    def __init__(self):
        self.avatar_handlers: AvatarHandlers
        self.transcript_handlers: TranscriptHandlers
        # ...
```

### 1.2. Database Layer
```python
class DatabaseManager:
    """Управление подключениями к БД"""
    def __init__(self):
        self.engine: AsyncEngine
        self.session_factory: sessionmaker

    async def get_session(self) -> AsyncSession:
        """Получение сессии БД"""

class BaseRepository:
    """Базовый класс для всех репозиториев"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: Any) -> Optional[Model]:
        """Получение записи по ID"""

    async def create(self, data: Dict) -> Model:
        """Создание новой записи"""

    async def update(self, id: Any, data: Dict) -> Model:
        """Обновление записи"""

    async def delete(self, id: Any) -> bool:
        """Удаление записи"""

class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получение пользователя по Telegram ID"""

class AvatarRepository(BaseRepository):
    """Репозиторий для работы с аватарами"""
    async def get_user_avatars(self, user_id: int) -> List[Avatar]:
        """Получение всех аватаров пользователя"""
```

### 1.3. Storage Layer
```python
class StorageManager:
    """Управление файловым хранилищем"""
    def __init__(self):
        self.minio_client: MinioClient
        self.local_storage: LocalStorage

class MinioClient:
    """Клиент для работы с MinIO"""
    async def upload_file(self, bucket: str, path: str, data: bytes) -> str:
        """Загрузка файла"""

    async def download_file(self, bucket: str, path: str) -> bytes:
        """Скачивание файла"""

class LocalStorage:
    """Временное локальное хранилище"""
    async def save_temp_file(self, data: bytes) -> str:
        """Сохранение временного файла"""
```

### 1.4. Service Layer
```python
class BaseService:
    """Базовый класс для всех сервисов"""
    def __init__(self, db: DatabaseManager, storage: StorageManager):
        self.db = db
        self.storage = storage

class UserService(BaseService):
    """Сервис для работы с пользователями"""
    async def register_user(self, telegram_data: Dict) -> User:
        """Регистрация нового пользователя"""

class AvatarService(BaseService):
    """Сервис для работы с аватарами"""
    async def create_avatar(self, user_id: int, photos: List[bytes]) -> Avatar:
        """Создание нового аватара"""

class StateManager(BaseService):
    """Управление состояниями"""
    async def set_state(self, user_id: int, state: str):
        """Установка состояния"""
```

### 1.5. Handler Layer
```python
class BaseHandler:
    """Базовый класс для всех обработчиков"""
    def __init__(self, services: ServiceContainer):
        self.services = services

class AvatarHandlers(BaseHandler):
    """Обработчики для работы с аватарами"""
    async def handle_create_avatar(self, message: Message):
        """Обработка создания аватара"""

    async def handle_avatar_photo(self, message: Message):
        """Обработка загрузки фото"""

class TranscriptHandlers(BaseHandler):
    """Обработчики для работы с транскриптами"""
    async def handle_transcribe(self, message: Message):
        """Обработка транскрибации"""
```

## 2. План миграции

### 2.1. Подготовительный этап
1. Создать новую ветку `feature/oop-refactoring`
2. Подготовить тесты для критических компонентов
3. Создать базовые классы и интерфейсы
4. Настроить DI-контейнер
5. Создать интерфейсы для Backend API
6. Настроить моки для тестирования Backend API

### 2.2. Миграция слоя данных
1. Создать `DatabaseManager`
2. Перенести все репозитории на `BaseRepository`
3. Реализовать новые репозитории:
   - UserRepository
   - AvatarRepository
   - TranscriptRepository
   - StateRepository
4. Обновить модели для работы с новыми репозиториями

### 2.3. Миграция хранилища
1. Создать `StorageManager`
2. Реализовать `MinioClient`
3. Реализовать `LocalStorage`
4. Перенести всю работу с файлами на новые классы

### 2.4. Миграция сервисов
1. Создать `ServiceContainer`
2. Реализовать базовые сервисы:
   - UserService
   - AvatarService
   - TranscriptService
   - StateManager
3. Перенести бизнес-логику в соответствующие сервисы
4. Обновить зависимости между сервисами

### 2.5. Миграция обработчиков
1. Создать `HandlerContainer`
2. Реализовать базовые обработчики:
   - AvatarHandlers
   - TranscriptHandlers
   - GeneralHandlers
3. Перенести логику обработчиков в новые классы
4. Обновить регистрацию обработчиков

### 2.6. Интеграция
1. Создать основной класс `AishaBot`
2. Реализовать инициализацию всех компонентов
3. Настроить DI и управление зависимостями
4. Реализовать graceful shutdown

### 2.7. Тестирование
1. Обновить существующие тесты
2. Добавить тесты для новых классов
3. Настроить моки для тестирования
4. Провести интеграционное тестирование

### 2.8. Документация
1. Обновить архитектурную документацию
2. Добавить UML-диаграммы
3. Обновить API-документацию
4. Обновить инструкции по развертыванию

## 3. Критерии готовности

### 3.1. Код
- [ ] Все компоненты переведены на ООП
- [ ] Соблюдены принципы SOLID
- [ ] Реализована корректная обработка ошибок
- [ ] Добавлено логирование

### 3.2. Тесты
- [ ] Все критические компоненты покрыты тестами
- [ ] Тесты проходят успешно
- [ ] Достигнуто покрытие кода > 80%

### 3.3. Документация
- [ ] Обновлена вся документация
- [ ] Добавлены диаграммы классов
- [ ] Описаны все публичные интерфейсы

### 3.4. Производительность
- [ ] Нет утечек памяти
- [ ] Время отклика не увеличилось
- [ ] Корректная работа с БД

## 4. Этапы внедрения

### 4.1. Фаза 1: Базовая структура
1. Создание базовых классов
2. Настройка DI
3. Базовая документация

### 4.2. Фаза 2: Критические компоненты
1. Миграция БД и хранилища
2. Основные сервисы
3. Базовые обработчики

### 4.3. Фаза 3: Расширенный функционал
1. Дополнительные сервисы
2. Все обработчики
3. Полная интеграция

### 4.4. Фаза 4: Финализация
1. Полное тестирование
2. Документация
3. Развертывание

## 5. Риски и митигация

### 5.1. Технические риски
- Проблемы с производительностью
- Конфликты зависимостей
- Утечки памяти

### 5.2. Митигация
- Поэтапное внедрение
- Тщательное тестирование
- Мониторинг метрик

## 6. Временные рамки

### 6.1. Оценка времени
- Подготовка: 1 неделя
- Базовая структура: 2 недели
- Миграция компонентов: 4 недели
- Тестирование: 2 недели
- Документация: 1 неделя

### 6.2. Общая продолжительность
Ориентировочно: 10 недель

## 7. Мониторинг прогресса

### 7.1. Метрики
- Количество перенесенных компонентов
- Покрытие тестами
- Количество багов
- Время отклика системы

### 7.2. Чек-поинты
- Еженедельные ревью кода
- Ежедневные статус-апдейты
- Регулярные тесты производительности
