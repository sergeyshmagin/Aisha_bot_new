# 📋 План интеграции Imagen 4 в Aisha Bot

## 🎯 Цель
Интегрировать Google Imagen 4 API для генерации изображений по описанию с полным сохранением в единую галерею.

## 📊 Анализ текущей архитектуры

### ✅ Что уже есть:
- **Prompt Optimizer** (`app/services/generation/prompt_processing_service.py`)
- **База данных** с моделью `ImageGeneration` 
- **Галерея** с фильтрами (в `app/handlers/gallery/`)
- **MinIO** для хранения файлов (192.168.0.4)
- **Redis** для кеширования (192.168.0.3)
- **PostgreSQL** для метаданных (192.168.0.4)

### 🔄 Текущий flow галереи:
1. Пользователь генерирует изображение с аватаром
2. Результат сохраняется в `ImageGeneration` 
3. Файлы загружаются в MinIO
4. Галерея показывает все генерации с фильтрами

### 📋 Текущие фильтры галереи:
- **🔍 Фильтры** → `gallery_filters` (базовая заглушка)
- **📊 Статистика** → `gallery_stats`
- **📅 По дате** → (в разработке)
- **🎭 По аватару** → (в разработке)
- **📝 По промпту** → (в разработке)
- **💛 Избранные** → (в разработке)

## 🚀 План реализации

### 📝 Этап 1: Создание Imagen 4 сервиса

#### 1.1 Новый API сервис
```
app/services/generation/imagen4/
├── imagen4_service.py      # Основной сервис
├── image_processor.py      # Обработка изображений
└── models.py              # Модели данных
```

#### 1.2 Установка зависимости
```bash
pip install fal-client
```

#### 1.3 Конфигурация
Добавить в `app/core/config.py`:
```python
# Imagen 4 Settings
IMAGEN4_API_KEY: str = Field(env="FAL_KEY")
IMAGEN4_ENABLED: bool = Field(True, env="IMAGEN4_ENABLED")
IMAGEN4_DEFAULT_ASPECT_RATIO: str = Field("1:1", env="IMAGEN4_DEFAULT_ASPECT_RATIO")
IMAGEN4_MAX_IMAGES: int = Field(4, env="IMAGEN4_MAX_IMAGES")
IMAGEN4_GENERATION_COST: float = Field(5.0, env="IMAGEN4_GENERATION_COST")
```

### 📝 Этап 2: Расширение модели ImageGeneration

#### 2.1 Добавление полей типа генерации
Модифицировать `app/database/models/generation.py`:
```python
# Добавить поля:
generation_type: Mapped[str] = mapped_column(String(50), default="avatar")  # "avatar" | "imagen4"
source_model: Mapped[str] = mapped_column(String(100), nullable=True)       # "fal-ai/imagen4/preview"
```

#### 2.2 Создание миграции
```python
# В новой миграции:
def upgrade():
    op.add_column('image_generations', sa.Column('generation_type', sa.String(50), default='avatar'))
    op.add_column('image_generations', sa.Column('source_model', sa.String(100), nullable=True))
```

### 📝 Этап 3: Обновление существующей галереи

#### 3.1 Модификация `ImageGenerationRepository`
Добавить методы фильтрации:
```python
async def get_user_images_by_type(
    self, 
    user_id: UUID, 
    generation_type: str = None,
    limit: int = 50
) -> List[ImageGeneration]:
    """Получить изображения по типу генерации"""
```

#### 3.2 Обновление фильтров галереи
Модифицировать `app/handlers/gallery/keyboards.py`:
```python
def build_gallery_filter_buttons() -> List[List[InlineKeyboardButton]]:
    """Строит кнопки фильтров с учетом новых типов"""
    return [
        [
            InlineKeyboardButton(text="📸 Фото со мной", callback_data="filter_type_avatar"),
            InlineKeyboardButton(text="🖼️ Изображения", callback_data="filter_type_imagen4")
        ],
        [
            InlineKeyboardButton(text="🎥 Видео", callback_data="filter_type_video"),
            InlineKeyboardButton(text="📋 Все", callback_data="filter_type_all")
        ]
    ]
```

#### 3.3 Реализация в `filter_handler.py`
```python
@router.callback_query(F.data.startswith("filter_type_"))
async def handle_type_filter(callback: CallbackQuery, state: FSMContext):
    """Обработчик фильтра по типу генерации"""
    generation_type = callback.data.replace("filter_type_", "")
    
    if generation_type == "all":
        generation_type = None
    
    # Получаем отфильтрованные изображения
    # Показываем галерею с фильтром
```

### 📝 Этап 4: Imagen 4 генерация

#### 4.1 Обработчики 
```
app/handlers/generation/imagen4/
├── __init__.py
├── main_handler.py        # Основной обработчик  
├── prompt_handler.py      # Обработка промптов
└── states.py             # FSM состояния
```

#### 4.2 FSM состояния
```python
class Imagen4States(StatesGroup):
    waiting_prompt = State()
    selecting_aspect_ratio = State()
    selecting_count = State()
    confirming_generation = State()
```

#### 4.3 Процесс генерации
1. **Кнопка "📝 По описанию"** → Начало процесса
2. **Ввод промпта** → Использование существующего Prompt Optimizer
3. **Выбор параметров** → Aspect ratio, количество изображений
4. **Подтверждение** → Показ оптимизированного промпта + стоимость
5. **Генерация** → Отправка в Imagen 4 API 
6. **Сохранение** → MinIO + PostgreSQL с `generation_type="imagen4"`
7. **Результат** → Показ в чате + переход в галерею

#### 4.4 Интеграция в меню творчества
Модифицировать существующую клавиатуру:
```python
# В app/keyboards/creativity.py добавить:
[
    InlineKeyboardButton(text="📝 По описанию", callback_data="imagen4_start")
]
```

### 📝 Этап 5: UX оптимизация (для аудитории 40+)

#### 5.1 Простые тексты
```python
IMAGEN4_TEXTS = {
    "welcome": """✍️ <b>Создание изображения</b>

📝 <b>Опишите что хотите увидеть:</b>

💡 <b>Примеры:</b>
• Красивый закат над морем
• Котенок играет с мячиком  
• Современный офис с большими окнами
• Букет роз на столе""",

    "processing": """⏳ <b>Обрабатываю ваш запрос...</b>

🔄 Улучшаю описание для лучшего результата""",

    "generating": """🎨 <b>Создаю изображение...</b>

⏳ Это может занять 30-60 секунд
📱 Можете продолжить работу в боте""",

    "ready": """✅ <b>Готово!</b>

📸 Изображение создано и сохранено в галерею
🎭 Результат получился отличный!"""
}
```

#### 5.2 Показ процесса в реальном времени
```python
async def update_generation_status(user_id: int, status: str):
    """Обновление статуса генерации в реальном времени"""
    # Использовать существующую систему уведомлений
```

### 📝 Этап 6: Единая галерея с типизацией

#### 6.1 Обновление `GalleryViewer`
```python
async def show_gallery_main(
    self, 
    callback: CallbackQuery, 
    state: FSMContext,
    generation_type: str = None  # Новый параметр фильтрации
):
    """Показ галереи с возможностью фильтрации по типу"""
```

#### 6.2 Обновление карточек изображений
Добавить индикаторы типа в `card_formatter.py`:
```python
def format_image_card(generation: ImageGeneration) -> str:
    """Форматирование карточки с типом генерации"""
    type_icon = {
        "avatar": "👤",
        "imagen4": "🎨", 
        "video": "🎥"
    }.get(generation.generation_type, "📸")
    
    return f"{type_icon} {existing_format}"
```

#### 6.3 Статистика с разбивкой по типам
Обновить `stats.py`:
```python
async def get_gallery_stats_by_type(user_id: UUID) -> Dict:
    """Статистика с разбивкой по типам генерации"""
    return {
        "avatar_count": count_by_type("avatar"),
        "imagen4_count": count_by_type("imagen4"),
        "video_count": count_by_type("video"),
        "total_count": total_count
    }
```

## 🗂️ Структура файлов

```
app/
├── services/generation/imagen4/           # НОВОЕ
│   ├── __init__.py
│   ├── imagen4_service.py
│   ├── image_processor.py  
│   └── models.py
├── handlers/generation/imagen4/           # НОВОЕ
│   ├── __init__.py
│   ├── main_handler.py
│   ├── prompt_handler.py
│   └── states.py
├── handlers/gallery/                      # ОБНОВИТЬ
│   ├── filter_handler.py                 # Добавить фильтры по типу
│   ├── keyboards.py                       # Добавить кнопки типов
│   └── gallery_viewer.py                 # Поддержка фильтрации
├── keyboards/                             # ОБНОВИТЬ
│   ├── creativity.py                      # Добавить "📝 По описанию"
│   └── imagen4.py                        # НОВОЕ
└── database/migrations/                   # НОВОЕ
    └── add_generation_type_fields.py
```

## 🤔 Решение по архитектуре галереи

### ✅ Рекомендация: ЕДИНАЯ галерея с типизацией

**Преимущества:**
1. **Простота для пользователя** - одно место для всех изображений
2. **Меньше дублирования кода** - переиспользование существующей галереи
3. **Единая навигация** - привычные кнопки и управление  
4. **Легкое масштабирование** - добавление новых типов (видео, etc.)
5. **UX для 40+** - не нужно изучать разные интерфейсы

**Реализация:**
- Добавить поле `generation_type` в `ImageGeneration`
- Обновить фильтры: "📸 Фото со мной" / "🖼️ Изображения" / "🎥 Видео"
- Сохранить все существующие функции галереи
- Добавить визуальные индикаторы типа контента

## 📋 Детальные задачи

### 🔧 Backend (2-3 дня)
1. [ ] Создать Imagen 4 API сервис
2. [ ] Добавить поля `generation_type`, `source_model` в `ImageGeneration`
3. [ ] Создать миграцию БД
4. [ ] Обновить `ImageGenerationRepository` для фильтрации по типу
5. [ ] Интегрировать с существующим Prompt Optimizer
6. [ ] Настроить сохранение в MinIO с типизацией

### 🎮 Frontend (Bot) (2-3 дня)
1. [ ] Добавить кнопку "📝 По описанию" в меню творчества
2. [ ] Создать FSM состояния для Imagen 4
3. [ ] Создать обработчики prompt'ов с UX для 40+
4. [ ] Обновить фильтры галереи: добавить кнопки типов
5. [ ] Обновить карточки изображений с индикаторами типа
6. [ ] Обновить статистику с разбивкой по типам

### 🧪 Тестирование (1 день)
1. [ ] Unit тесты для Imagen 4 сервиса
2. [ ] Интеграционные тесты API
3. [ ] Тесты UX сценариев
4. [ ] Тесты единой галереи с новыми типами

## ⚙️ Конфигурация окружения

```bash
# Добавить в .env
FAL_KEY=your_fal_api_key_here
IMAGEN4_ENABLED=true
IMAGEN4_DEFAULT_ASPECT_RATIO=1:1
IMAGEN4_MAX_IMAGES=4
IMAGEN4_GENERATION_COST=5.0
```

## 🚦 Этапы развертывания

### 📚 Этап 1: Подготовка (1-2 дня)
- Создание Imagen 4 API сервиса
- Миграция БД (добавление полей типизации)
- Обновление существующих записей: `generation_type="avatar"`

### 🎯 Этап 2: Core функционал (2-3 дня)  
- Обработчики Imagen 4 с FSM
- Интеграция с существующим Prompt Optimizer
- Базовая генерация с сохранением `generation_type="imagen4"`

### 🎨 Этап 3: Галерея и UX (1-2 дня)
- Обновление фильтров галереи
- Индикаторы типов в карточках
- UX оптимизация для аудитории 40+
- Обновленная статистика

### 🚀 Этап 4: Deployment (1 день)
- Финальное тестирование
- Деплой через Docker registry на 192.168.0.4
- Мониторинг и отладка

## ✅ Принятые решения

1. **Кредиты**: **5 кредитов** за Imagen 4 генерацию
2. **Лимиты**: **Нет ограничений** - только баланс пользователя
3. **Качество**: **Не использовать** quality presets - стандартное качество
4. **Модерация**: Нужна ли проверка контента перед генерацией? (TBD)
5. **Fallback**: Что делать если Imagen 4 недоступен? (TBD)

## 🎯 Результат

После реализации пользователи смогут:
- Генерировать изображения по текстовому описанию через кнопку "📝 По описанию"
- Использовать автоматическую оптимизацию промптов (существующий сервис)
- Просматривать ВСЕ результаты в единой галерее
- Фильтровать: "📸 Фото со мной" (аватары) / "🖼️ Изображения" (Imagen 4) / "🎥 Видео"
- Получать высококачественные результаты от Google Imagen 4
- Пользоваться знакомым интерфейсом галереи без изучения нового

Все это с сохранением простого UX для аудитории 40+ и переиспользованием существующей архитектуры. 