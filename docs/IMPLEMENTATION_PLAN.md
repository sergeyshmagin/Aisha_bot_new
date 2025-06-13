# План реализации новых функций Aisha Bot v2.1

## 🎯 Общая стратегия

Поэтапное внедрение новых возможностей с минимальным риском для стабильности системы.

## 📋 Приоритеты разработки

### Фаза 1: Imagen4 и улучшенная галерея (2-3 недели)
**Приоритет: ВЫСОКИЙ**

#### 1.1 Интеграция Imagen4 (FAL AI)
- ✅ Изучить FAL AI API для Imagen4
- ⏳ Создать сервис `app/services/imagen4_service.py`
- ⏳ Добавить хэндлеры для Imagen4 генерации
- ⏳ Реализовать прогресс-бар для генерации
- ⏳ Интегрировать с системой кредитов

#### 1.2 Анализ фото → Промпт (GPT-4 Vision)
- ✅ Использовать существующий OpenAI Vision
- ⏳ Создать хэндлер для загрузки фото
- ⏳ Генерировать промпты из изображений
- ⏳ Предлагать генерацию на основе анализа

#### 1.3 Улучшенная галерея
- ⏳ Разделить галерею по типам (аватары/Imagen4/анализ)
- ⏳ Добавить фильтры и поиск
- ⏳ Реализовать экспорт в высоком качестве

**Техническая реализация:**
```python
# app/services/imagen4_service.py
class Imagen4Service:
    async def generate_image(self, prompt: str, style: str = "photorealistic") -> str
    async def get_generation_status(self, task_id: str) -> dict
    async def estimate_cost(self, params: dict) -> int

# app/handlers/imagen4.py  
@router.callback_query(F.data == "imagen4_generation")
async def start_imagen4_flow(call: CallbackQuery, state: FSMContext)

# app/states/creation.py
class Imagen4States(StatesGroup):
    prompt = State()
    style = State() 
    advanced_params = State()
```

### Фаза 2: Видео генерация (3-4 недели)
**Приоритет: ВЫСОКИЙ**

#### 2.1 Hedra AI интеграция
- ⏳ Подключить Hedra AI API
- ⏳ Реализовать загрузку фото для анимации
- ⏳ Создать интерфейс для ввода текста/речи
- ⏳ Добавить preview перед генерацией

#### 2.2 Kling 2.1 Pro (FAL AI)
- ⏳ Интегрировать Kling через FAL AI
- ⏳ Реализовать различные стили видео
- ⏳ Добавить контроль длительности (до 10с)
- ⏳ Оптимизировать для мобильных устройств

#### 2.3 Weo3 Creative (FAL AI)
- ⏳ Подключить Weo3 API
- ⏳ Реализовать креативные эффекты
- ⏳ Интегрировать с существующими изображениями

#### 2.4 Видео галерея
- ⏳ Создать отдельную галерею для видео
- ⏳ Добавить превью и метаданные
- ⏳ Реализовать сжатие для Telegram

**Техническая реализация:**
```python
# app/services/video_service.py
class VideoService:
    async def create_hedra_video(self, image_path: str, text: str) -> str
    async def create_kling_video(self, prompt: str, duration: int) -> str
    async def create_weo3_video(self, prompt: str, style: str) -> str
    async def compress_for_telegram(self, video_path: str) -> str

# app/models/video.py
class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String)  # hedra, kling, weo3
    prompt = Column(Text)
    file_path = Column(String)
    thumbnail_path = Column(String)
    duration = Column(Float)
    created_at = Column(DateTime)
```

### Фаза 3: Парсинг новостей (4-5 недель)
**Приоритет: СРЕДНИЙ**

#### 3.1 Telegram каналы парсер
- ⏳ Создать парсер Telegram каналов
- ⏳ Реализовать подписки пользователей
- ⏳ Добавить фильтрацию контента
- ⏳ Создать систему уведомлений

#### 3.2 AI анализ трендов
- ⏳ Интегрировать OpenAI для анализа новостей
- ⏳ Выявлять trending темы
- ⏳ Генерировать insights и рекомендации
- ⏳ Создавать дайджесты

#### 3.3 Контент на основе новостей
- ⏳ Генерировать изображения по новостям
- ⏳ Создавать информографику
- ⏳ Предлагать креативные интерпретации

**Техническая реализация:**
```python
# app/services/news_service.py
class NewsService:
    async def parse_channel(self, channel_username: str) -> List[NewsItem]
    async def analyze_trends(self, timeframe: str) -> List[Trend]
    async def generate_content_ideas(self, news_item: NewsItem) -> List[str]
    async def create_digest(self, user_id: int, timeframe: str) -> str

# app/models/news.py
class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    title = Column(String)
    last_parsed = Column(DateTime)

class NewsItem(Base):
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    message_id = Column(Integer)
    text = Column(Text)
    images = Column(JSON)
    views = Column(Integer)
    created_at = Column(DateTime)

class UserChannel(Base):
    __tablename__ = "user_channels"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), primary_key=True)
    subscribed_at = Column(DateTime)
```

### Фаза 4: Аудио возможности (2-3 недели)
**Приоритет: НИЗКИЙ**

#### 4.1 TTS озвучка
- ⏳ Интегрировать ElevenLabs или OpenAI TTS
- ⏳ Добавить выбор голосов
- ⏳ Реализовать настройки речи
- ⏳ Сохранение аудиофайлов

#### 4.2 Генерация музыки
- ⏳ Исследовать Suno AI или аналоги
- ⏳ Создать интерфейс для музыкальных промптов
- ⏳ Добавить предварительное прослушивание

## 🛠️ Техническая архитектура

### Новые сервисы
```
app/services/
├── imagen4_service.py      # Imagen4 генерация
├── video_service.py        # Видео генерация (Hedra, Kling, Weo3)
├── news_service.py         # Парсинг и анализ новостей
├── content_service.py      # Генерация контента из новостей
└── audio_service.py        # TTS и музыка
```

### Новые модели данных
```
app/models/
├── video.py               # Видео контент
├── news.py               # Новости и каналы
├── content_generation.py # История генераций
└── user_preferences.py   # Пользовательские настройки
```

### Новые хэндлеры
```
app/handlers/
├── imagen4.py            # Imagen4 генерация
├── video/                # Видео генерация
│   ├── hedra.py
│   ├── kling.py
│   └── weo3.py
├── news/                 # Новости
│   ├── channels.py
│   ├── trending.py
│   └── content.py
└── audio/               # Аудио функции
    ├── tts.py
    └── music.py
```

## 🔄 CI/CD процесс

### Тестирование
- Юнит-тесты для каждого сервиса
- Интеграционные тесты с внешними API
- E2E тесты пользовательских сценариев
- Нагрузочное тестирование

### Развертывание
1. Тестирование в dev-окружении
2. Staging с реальными API
3. Постепенный rollout в production
4. Мониторинг метрик и ошибок

## 📊 Метрики и мониторинг

### Ключевые метрики
- Время генерации контента
- Конверсия использования новых функций
- Качество сгенерированного контента (оценки пользователей)
- Стоимость API запросов

### Системы мониторинга
- Prometheus + Grafana для технических метрик
- Sentry для отслеживания ошибок
- Логирование всех API вызовов
- Алерты на критичные события

## 💰 Экономическая модель

### Стоимость новых функций
- **Imagen4**: 15-20 кредитов за изображение
- **Hedra Video**: 50-70 кредитов за видео
- **Kling Video**: 80-100 кредитов за видео
- **Weo3 Video**: 60-80 кредитов за видео
- **Анализ фото**: 5 кредитов
- **TTS**: 2 кредита за минуту

### Пакеты кредитов
- **Starter**: 100 кредитов - 299₽
- **Creator**: 500 кредитов - 1299₽ 
- **Pro**: 1500 кредитов - 3499₽
- **Business**: 5000 кредитов - 9999₽

## 🚀 Quick Wins (можно реализовать быстро)

1. **Анализ фото → Промпт** (1-2 дня)
   - Использует существующий GPT-4 Vision
   - Минимальные изменения в коде

2. **Imagen4 базовая версия** (3-5 дней)
   - FAL AI уже интегрирован
   - Нужно только добавить новый endpoint

3. **Улучшенная навигация** (1 день)
   - Новые кнопки уже созданы
   - Нужно протестировать UX

4. **Видео галерея** (2-3 дня)
   - Адаптировать существующую галерею
   - Добавить video preview

Этот план обеспечивает пошаговое развитие продукта с минимальными рисками и максимальной ценностью для пользователей!