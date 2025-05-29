# 🎨 Улучшенная система генерации изображений

## 📋 Анализ текущего состояния

### 🔍 Проблемы текущей системы

1. **Разделение функций**: Галерея и аватары смешаны в одном меню
2. **Неиспользуемая галерея**: Кнопка "🖼 Галерея" в главном меню не используется
3. **Сложный UX**: Пользователю нужно много кликов для генерации
4. **Отсутствие шаблонов**: Нет готовых стилей и образов
5. **Нет истории**: Сгенерированные изображения не сохраняются
6. **Отсутствие контроля затрат**: Нет системы баланса для ограничения использования

### 🎯 Анализ конкурентов

По скриншотам конкурента видно:
- **Галерея стилей** в каждом разделе (Женский, Мужской, Портрет, Стильный и т.д.)
- **Готовые образы** с превью изображений
- **Простой выбор**: Клик на образ → генерация
- **Категоризация**: Четкое разделение по типам (Деловой, Праздники, Город и т.д.)
- **Настройки генерации**: Формат фото, количество, качество

---

## 🚀 Новая архитектура системы

### 💰 Система баланса

**Стоимость генерации: 50 единиц за изображение**

- ✅ Проверка баланса перед генерацией
- ✅ Автоматическое списание при запуске
- ✅ Возврат средств при ошибке генерации
- ✅ Отображение баланса в интерфейсе
- ✅ Блокировка функций при недостатке средств

### 📱 Обновленное главное меню

```
┌─────────────────────────────────────┐
│           🤖 Aisha Bot              │
├─────────────────────────────────────┤
│ 🎨 Создать изображение              │  ← НОВОЕ: Основная функция
│ 🎭 Мои аватары                      │  ← Управление аватарами
│ 🖼️ Моя галерея                     │  ← История генераций
│ 🎤 Транскрибация                    │  ← Существующая функция
│ ❓ Помощь                           │
└─────────────────────────────────────┘
```

### 🎨 Меню "Создать изображение"

```
┌─────────────────────────────────────┐
│ 🎨 Создание изображения             │
│ 👤 Основной аватар: Анна (Портрет)  │
│ 💰 Баланс: 500 единиц               │  ← НОВОЕ: Отображение баланса
│ 💎 Стоимость: 50 единиц за изображение │ ← НОВОЕ: Стоимость
├─────────────────────────────────────┤
│ 🔥 Популярные стили                 │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│ │ 🏢  │ │ 🌟  │ │ 🎭  │ │ 🎨  │    │
│ │Бизнес│ │Гламур│ │Театр│ │ Арт │    │
│ └─────┘ └─────┘ └─────┘ └─────┘    │
├─────────────────────────────────────┤
│ 📂 Все категории                    │
│ • 👔 Деловой стиль                  │
│ • 🎉 Праздники                      │
│ • 🏙️ Городской стиль                │
│ • 🌿 Природа                        │
│ • 🎭 Творчество                     │
│ • 🚀 Фантастика                     │
├─────────────────────────────────────┤
│ ✨ Мои избранные (3)                │
│ 📝 Свой промпт                      │
│ 🔄 Сменить аватар                   │
│ 🖼️ Моя галерея                     │  ← НОВОЕ: Быстрый доступ
└─────────────────────────────────────┘
```

### 💳 Недостаточно баланса

```
┌─────────────────────────────────────┐
│ 🎨 Создание изображения             │
│ 👤 Основной аватар: Анна (Портрет)  │
│ 💰 Баланс: 25 единиц                │  ← Недостаточно средств
│ 💎 Стоимость: 50 единиц за изображение │
├─────────────────────────────────────┤
│ ⚠️ Недостаточно средств для генерации │
├─────────────────────────────────────┤
│ 💰 Пополнить баланс                 │  ← Кнопка пополнения
├─────────────────────────────────────┤
│ 🔄 Сменить аватар                   │
│ 🖼️ Моя галерея                     │
│ 🔙 Главное меню                     │
└─────────────────────────────────────┘
```

### 🎭 Меню "Мои аватары"

```
┌─────────────────────────────────────┐
│ 🎭 Управление аватарами             │
├─────────────────────────────────────┤
│ 🆕 Создать новый аватар             │
├─────────────────────────────────────┤
│ 📋 Мои аватары (2)                  │
│                                     │
│ ⭐ Анна (Портретный)                │
│    ✅ Готов • Основной              │
│    [🎨 Создать] [⚙️ Настройки]     │
│                                     │
│ 🎨 Художник (Стилевой)              │
│    🔄 Обучается... 45%              │
│    [📊 Статус] [⚙️ Настройки]      │
└─────────────────────────────────────┘
```

### 🖼️ Меню "Моя галерея"

```
┌─────────────────────────────────────┐
│ 🖼️ Моя галерея                     │
├─────────────────────────────────────┤
│ 📊 Статистика                       │
│ • Всего изображений: 24             │
│ • За этот месяц: 8                  │
│ • Любимый стиль: Деловой            │
├─────────────────────────────────────┤
│ 🗂️ Категории                       │
│ • 👔 Деловые (8)                    │
│ • 🎨 Творческие (5)                 │
│ • 🎉 Праздничные (3)                │
│ • 🌟 Другие (8)                     │
├─────────────────────────────────────┤
│ 🔍 Поиск по тегам                   │
│ 📅 Сортировка по дате               │
└─────────────────────────────────────┘
```

---

## 🎯 Детальный UX Flow

### 1. Создание изображения → Выбор категории

```
🎨 Создание изображения
    ↓ (клик на "👔 Деловой стиль")
    
┌─────────────────────────────────────┐
│ ← 👔 Деловой стиль                  │
├─────────────────────────────────────┤
│ 🏢 Офисные образы                   │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│ │ 📊  │ │ 💼  │ │ 🤝  │ │ 📈  │    │
│ │Презен│ │Перего│ │Встреча│ │Успех │    │
│ │тация │ │воры │ │     │ │     │    │
│ └─────┘ └─────┘ └─────┘ └─────┘    │
├─────────────────────────────────────┤
│ 👗 Дресс-код                        │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│ │ 👔  │ │ 👗  │ │ 🧥  │ │ 👠  │    │
│ │Строгий│ │Элегант│ │Casual│ │Формал│    │
│ └─────┘ └─────┘ └─────┘ └─────┘    │
├─────────────────────────────────────┤
│ 🎯 Специальные                      │
│ • 🎤 Выступление                    │
│ • 📸 Корпоративное фото             │
│ • 🏆 Награждение                    │
└─────────────────────────────────────┘
```

### 2. Выбор конкретного образа

```
Клик на "📊 Презентация"
    ↓
    
┌─────────────────────────────────────┐
│ 📊 Презентация                      │
├─────────────────────────────────────┤
│        [ПРЕВЬЮ ИЗОБРАЖЕНИЯ]         │
│                                     │
├─────────────────────────────────────┤
│ 📝 Промпт:                          │
│ "professional presentation, business │
│ attire, confident pose, office      │
│ background, studio lighting"        │
├─────────────────────────────────────┤
│ ⚙️ Настройки генерации              │
│ • Качество: ⚡ Быстро               │
│ • Формат: 📱 Портрет (3:4)          │
│ • Количество: 1 изображение         │
├─────────────────────────────────────┤
│ 🎨 Создать изображение              │
│ 📝 Изменить промпт                  │
│ ❤️ В избранное                      │
└─────────────────────────────────────┘
```

### 3. Настройки генерации

```
Клик на "⚙️ Настройки генерации"
    ↓
    
┌─────────────────────────────────────┐
│ ⚙️ Настройки генерации              │
├─────────────────────────────────────┤
│ 🎯 Качество:                        │
│ ○ ⚡ Быстро (15-25с)                │
│ ● ⚖️ Сбалансированно (25-35с)       │
│ ○ 💎 Высокое (40-60с)               │
│ ○ 🚀 Ultra 2K (60-90с)              │
├─────────────────────────────────────┤
│ 📐 Формат:                          │
│ ○ 📱 Портрет (3:4)                  │
│ ● 🖼️ Квадрат (1:1)                 │
│ ○ 🖥️ Альбом (4:3)                  │
│ ○ 📺 Широкий (16:9)                 │
├─────────────────────────────────────┤
│ 🔢 Количество: [1] [2] [3] [4]      │
├─────────────────────────────────────┤
│ 💰 Стоимость: ~0.05$ за изображение │
│ ⏱️ Время: ~25-35 секунд             │
├─────────────────────────────────────┤
│ ✅ Применить                        │
└─────────────────────────────────────┘
```

### 4. Процесс генерации

```
┌─────────────────────────────────────┐
│ 🎨 Создаю ваше изображение...       │
│                                     │
│ ████████████░░░░ 75%                │
│                                     │
│ ⚡ FLUX.1 Pro • Сбалансированное    │
│ 🎭 Аватар: Анна                     │
│ 📊 Стиль: Презентация               │
│                                     │
│ ⏱️ Осталось ~8 секунд               │
│                                     │
│ 💡 Пока ждете, посмотрите другие    │
│    стили в галерее!                 │
└─────────────────────────────────────┘
```

### 5. Результат с действиями

```
┌─────────────────────────────────────┐
│ ✨ Готово! Ваше изображение         │
├─────────────────────────────────────┤
│                                     │
│        [СГЕНЕРИРОВАННОЕ             │
│         ИЗОБРАЖЕНИЕ]                │
│                                     │
├─────────────────────────────────────┤
│ 💾 Сохранить в галерею              │
│ 🔄 Создать вариацию                 │
│ 📤 Поделиться                       │
│ ❤️ В избранное                      │
├─────────────────────────────────────┤
│ 📝 Промпт: "professional presenta..." │
│ 🎯 Стиль: Презентация               │
│ ⚡ Качество: Сбалансированное       │
│ 🕐 Время: 28 секунд                 │
├─────────────────────────────────────┤
│ 🎨 Создать еще                      │
│ 🔙 К выбору стилей                  │
└─────────────────────────────────────┘
```

---

## 🗂️ Структура категорий и стилей

### 👔 Деловой стиль

```python
BUSINESS_CATEGORY = {
    "id": "business",
    "name": "👔 Деловой стиль",
    "icon": "👔",
    "description": "Профессиональные образы для работы",
    "subcategories": {
        "office": {
            "name": "🏢 Офисные образы",
            "templates": [
                {
                    "id": "presentation",
                    "name": "📊 Презентация",
                    "prompt": "professional presentation, business attire, confident pose, office background, studio lighting",
                    "preview_url": "/previews/business_presentation.jpg",
                    "tags": ["презентация", "офис", "деловой"],
                    "popularity": 95
                },
                {
                    "id": "negotiation",
                    "name": "💼 Переговоры",
                    "prompt": "business meeting, professional attire, handshake, conference room, natural lighting",
                    "preview_url": "/previews/business_meeting.jpg",
                    "tags": ["переговоры", "встреча", "деловой"],
                    "popularity": 87
                }
            ]
        },
        "dresscode": {
            "name": "👗 Дресс-код",
            "templates": [
                {
                    "id": "formal",
                    "name": "👔 Строгий",
                    "prompt": "formal business attire, suit, professional headshot, corporate style",
                    "preview_url": "/previews/formal_business.jpg",
                    "tags": ["строгий", "костюм", "корпоративный"],
                    "popularity": 92
                }
            ]
        }
    }
}
```

### 🎉 Праздники

```python
CELEBRATION_CATEGORY = {
    "id": "celebration",
    "name": "🎉 Праздники",
    "icon": "🎉",
    "description": "Праздничные и торжественные образы",
    "subcategories": {
        "new_year": {
            "name": "🎄 Новый год",
            "templates": [
                {
                    "id": "new_year_party",
                    "name": "🥂 Новогодняя вечеринка",
                    "prompt": "new year celebration, festive attire, party atmosphere, champagne, elegant lighting",
                    "preview_url": "/previews/new_year_party.jpg",
                    "tags": ["новый год", "вечеринка", "праздник"],
                    "popularity": 89
                }
            ]
        },
        "birthday": {
            "name": "🎂 День рождения",
            "templates": [
                {
                    "id": "birthday_celebration",
                    "name": "🎈 Празднование",
                    "prompt": "birthday celebration, festive mood, cake, balloons, joyful expression",
                    "preview_url": "/previews/birthday.jpg",
                    "tags": ["день рождения", "торт", "праздник"],
                    "popularity": 76
                }
            ]
        }
    }
}
```

### 🏙️ Городской стиль

```python
URBAN_CATEGORY = {
    "id": "urban",
    "name": "🏙️ Городской стиль",
    "icon": "🏙️",
    "description": "Современные городские образы",
    "subcategories": {
        "street": {
            "name": "🚶 Уличный стиль",
            "templates": [
                {
                    "id": "street_fashion",
                    "name": "👟 Стрит-фэшн",
                    "prompt": "street fashion, urban style, casual wear, city background, natural lighting",
                    "preview_url": "/previews/street_fashion.jpg",
                    "tags": ["уличный", "мода", "город"],
                    "popularity": 84
                }
            ]
        },
        "cafe": {
            "name": "☕ В кафе",
            "templates": [
                {
                    "id": "coffee_shop",
                    "name": "☕ Кофейня",
                    "prompt": "coffee shop atmosphere, casual attire, cozy interior, warm lighting",
                    "preview_url": "/previews/coffee_shop.jpg",
                    "tags": ["кафе", "кофе", "уютно"],
                    "popularity": 78
                }
            ]
        }
    }
}
```

---

## 🔧 Техническая реализация

### 📊 Модели данных

```python
# app/database/models/generation.py

class StyleCategory(Base):
    """Категория стилей"""
    __tablename__ = "style_categories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Связи
    subcategories: Mapped[List["StyleSubcategory"]] = relationship(
        "StyleSubcategory", back_populates="category"
    )

class StyleSubcategory(Base):
    """Подкатегория стилей"""
    __tablename__ = "style_subcategories"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(50), ForeignKey("style_categories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Связи
    category: Mapped["StyleCategory"] = relationship("StyleCategory", back_populates="subcategories")
    templates: Mapped[List["StyleTemplate"]] = relationship(
        "StyleTemplate", back_populates="subcategory"
    )

class StyleTemplate(Base):
    """Шаблон стиля"""
    __tablename__ = "style_templates"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    subcategory_id: Mapped[str] = mapped_column(String(50), ForeignKey("style_subcategories.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(String(1000), nullable=False)
    preview_url: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Связи
    subcategory: Mapped["StyleSubcategory"] = relationship(
        "StyleSubcategory", back_populates="templates"
    )
    generations: Mapped[List["ImageGeneration"]] = relationship(
        "ImageGeneration", back_populates="template"
    )

class ImageGeneration(Base):
    """Генерация изображения"""
    __tablename__ = "image_generations"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    avatar_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("avatars.id"))
    template_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("style_templates.id"))
    
    # Промпты
    original_prompt: Mapped[str] = mapped_column(String(1000), nullable=False)
    final_prompt: Mapped[str] = mapped_column(String(1500), nullable=False)
    
    # Настройки
    quality_preset: Mapped[str] = mapped_column(String(50), default="balanced")
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="1:1")
    num_images: Mapped[int] = mapped_column(Integer, default=1)
    
    # Результат
    status: Mapped[GenerationStatus] = mapped_column(Enum(GenerationStatus))
    result_urls: Mapped[List[str]] = mapped_column(JSON, default=list)
    generation_time: Mapped[Optional[float]] = mapped_column(Float)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Пользовательские действия
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Связи
    user: Mapped["User"] = relationship("User")
    avatar: Mapped["Avatar"] = relationship("Avatar")
    template: Mapped[Optional["StyleTemplate"]] = relationship("StyleTemplate")

class GenerationStatus(str, Enum):
    """Статус генерации"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### 🎛️ Сервисы

```python
# app/services/generation/style_service.py

class StyleService:
    """Сервис для работы со стилями и шаблонами"""
    
    async def get_popular_categories(self, limit: int = 4) -> List[StyleCategory]:
        """Получает популярные категории"""
        # Возвращает категории отсортированные по популярности
        pass
    
    async def get_category_with_templates(self, category_id: str) -> Optional[StyleCategory]:
        """Получает категорию с шаблонами"""
        pass
    
    async def get_template_by_id(self, template_id: str) -> Optional[StyleTemplate]:
        """Получает шаблон по ID"""
        pass
    
    async def search_templates(self, query: str, limit: int = 10) -> List[StyleTemplate]:
        """Поиск шаблонов по тегам и названию"""
        pass
    
    async def get_user_favorites(self, user_id: UUID) -> List[StyleTemplate]:
        """Получает избранные шаблоны пользователя"""
        pass
    
    async def add_to_favorites(self, user_id: UUID, template_id: str) -> bool:
        """Добавляет шаблон в избранное"""
        pass

# app/services/generation/generation_service.py

class ImageGenerationService:
    """Сервис генерации изображений"""
    
    def __init__(self):
        self.fal_service = FALGenerationService()
        self.style_service = StyleService()
    
    async def generate_from_template(
        self,
        user_id: UUID,
        avatar_id: UUID,
        template_id: str,
        quality_preset: str = "balanced",
        aspect_ratio: str = "1:1",
        num_images: int = 1
    ) -> ImageGeneration:
        """Генерирует изображение по шаблону"""
        
        # Получаем шаблон
        template = await self.style_service.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Шаблон {template_id} не найден")
        
        # Получаем аватар
        avatar = await self._get_avatar(avatar_id, user_id)
        
        # Создаем запись генерации
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=template_id,
            original_prompt=template.prompt,
            final_prompt=self._build_final_prompt(template.prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        # Сохраняем в БД
        await self._save_generation(generation)
        
        # Запускаем генерацию асинхронно
        asyncio.create_task(self._process_generation(generation))
        
        return generation
    
    async def generate_custom(
        self,
        user_id: UUID,
        avatar_id: UUID,
        custom_prompt: str,
        quality_preset: str = "balanced",
        aspect_ratio: str = "1:1",
        num_images: int = 1
    ) -> ImageGeneration:
        """Генерирует изображение по кастомному промпту"""
        
        avatar = await self._get_avatar(avatar_id, user_id)
        
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=None,
            original_prompt=custom_prompt,
            final_prompt=self._build_final_prompt(custom_prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        await self._save_generation(generation)
        asyncio.create_task(self._process_generation(generation))
        
        return generation
    
    async def _process_generation(self, generation: ImageGeneration):
        """Обрабатывает генерацию"""
        try:
            # Обновляем статус
            generation.status = GenerationStatus.PROCESSING
            await self._update_generation(generation)
            
            # Получаем аватар
            avatar = await self._get_avatar(generation.avatar_id, generation.user_id)
            
            # Настройки генерации
            config = self._get_generation_config(
                generation.quality_preset,
                generation.aspect_ratio,
                generation.num_images
            )
            
            start_time = time.time()
            
            # Генерируем изображения
            if generation.num_images == 1:
                image_url = await self.fal_service.generate_avatar_image(
                    avatar=avatar,
                    prompt=generation.final_prompt,
                    generation_config=config
                )
                result_urls = [image_url] if image_url else []
            else:
                prompts = [generation.final_prompt] * generation.num_images
                result_urls = await self.fal_service.generate_multiple_images(
                    avatar=avatar,
                    prompts=prompts,
                    generation_config=config
                )
                result_urls = [url for url in result_urls if url]
            
            generation_time = time.time() - start_time
            
            # Обновляем результат
            generation.status = GenerationStatus.COMPLETED
            generation.result_urls = result_urls
            generation.generation_time = generation_time
            generation.completed_at = datetime.utcnow()
            
            await self._update_generation(generation)
            
            # Отправляем уведомление пользователю
            await self._notify_user(generation)
            
        except Exception as e:
            logger.exception(f"Ошибка генерации {generation.id}: {e}")
            
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            await self._update_generation(generation)
            
            # Уведомляем об ошибке
            await self._notify_error(generation)
```

### 🎨 Обработчики интерфейса

```python
# app/handlers/generation/main_handler.py

class GenerationMainHandler:
    """Главный обработчик генерации изображений"""
    
    def __init__(self):
        self.style_service = StyleService()
        self.generation_service = ImageGenerationService()
        self.avatar_service = AvatarService()
    
    async def show_generation_menu(self, callback: CallbackQuery):
        """Показывает главное меню генерации"""
        
        user_telegram_id = callback.from_user.id
        user = await self._get_user(user_telegram_id)
        
        # Получаем основной аватар
        main_avatar = await self.avatar_service.get_user_main_avatar(user.id)
        if not main_avatar:
            await callback.answer("❌ У вас нет основного аватара. Создайте аватар сначала!", show_alert=True)
            return
        
        # Получаем популярные категории
        popular_categories = await self.style_service.get_popular_categories(limit=4)
        
        # Получаем избранные шаблоны
        favorites = await self.style_service.get_user_favorites(user.id)
        
        # Формируем текст
        text = f"""🎨 **Создание изображения**
👤 Основной аватар: {main_avatar.name} ({main_avatar.training_type.value.title()})

🔥 **Популярные стили**"""
        
        # Формируем клавиатуру
        keyboard = self._build_generation_menu_keyboard(
            popular_categories, 
            favorites, 
            main_avatar.id
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    def _build_generation_menu_keyboard(
        self, 
        popular_categories: List[StyleCategory],
        favorites: List[StyleTemplate],
        avatar_id: UUID
    ) -> InlineKeyboardMarkup:
        """Строит клавиатуру главного меню генерации"""
        
        buttons = []
        
        # Популярные стили (2x2)
        if popular_categories:
            popular_buttons = []
            for i in range(0, len(popular_categories), 2):
                row = []
                for j in range(2):
                    if i + j < len(popular_categories):
                        cat = popular_categories[i + j]
                        row.append(InlineKeyboardButton(
                            text=f"{cat.icon} {cat.name.split(' ', 1)[1]}",  # Убираем эмодзи из названия
                            callback_data=f"gen_category:{cat.id}"
                        ))
                popular_buttons.append(row)
            buttons.extend(popular_buttons)
        
        # Все категории
        buttons.append([
            InlineKeyboardButton(
                text="📂 Все категории",
                callback_data="gen_all_categories"
            )
        ])
        
        # Избранные (если есть)
        if favorites:
            buttons.append([
                InlineKeyboardButton(
                    text=f"✨ Мои избранные ({len(favorites)})",
                    callback_data="gen_favorites"
                )
            ])
        
        # Свой промпт
        buttons.append([
            InlineKeyboardButton(
                text="📝 Свой промпт",
                callback_data=f"gen_custom:{avatar_id}"
            )
        ])
        
        # Сменить аватар
        buttons.append([
            InlineKeyboardButton(
                text="🔄 Сменить аватар",
                callback_data="gen_change_avatar"
            )
        ])
        
        # Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="main_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def show_category(self, callback: CallbackQuery):
        """Показывает категорию стилей"""
        
        category_id = callback.data.split(":")[1]
        category = await self.style_service.get_category_with_templates(category_id)
        
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        text = f"← {category.icon} **{category.name}**\n\n{category.description}"
        keyboard = self._build_category_keyboard(category)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    def _build_category_keyboard(self, category: StyleCategory) -> InlineKeyboardMarkup:
        """Строит клавиатуру категории"""
        
        buttons = []
        
        # Подкатегории и шаблоны
        for subcategory in category.subcategories:
            if not subcategory.is_active:
                continue
                
            # Заголовок подкатегории
            buttons.append([
                InlineKeyboardButton(
                    text=f"📁 {subcategory.name}",
                    callback_data="noop"
                )
            ])
            
            # Шаблоны подкатегории (2 в ряд)
            templates = [t for t in subcategory.templates if t.is_active]
            for i in range(0, len(templates), 2):
                row = []
                for j in range(2):
                    if i + j < len(templates):
                        template = templates[i + j]
                        row.append(InlineKeyboardButton(
                            text=template.name,
                            callback_data=f"gen_template:{template.id}"
                        ))
                buttons.append(row)
        
        # Назад
        buttons.append([
            InlineKeyboardButton(
                text="🔙 К выбору стилей",
                callback_data="generation_menu"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
```

---

## 📱 Обновленные клавиатуры

### Главное меню

```python
# app/keyboards/main.py

def get_main_menu() -> InlineKeyboardMarkup:
    """Создает обновленное главное меню бота"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Создать изображение",
                callback_data="generation_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 Мои аватары",
                callback_data="avatar_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼️ Моя галерея",
                callback_data="my_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎤 Транскрибация",
                callback_data="transcribe_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="main_help"
            )
        ]
    ])
```

---

## 🎯 План реализации

### Этап 1: Подготовка (1-2 дня)
- [ ] Создать модели данных для стилей и генераций
- [ ] Создать миграции БД
- [ ] Подготовить базовые категории и шаблоны
- [ ] Создать превью изображения для шаблонов

### Этап 2: Сервисы (2-3 дня)
- [ ] Реализовать StyleService
- [ ] Обновить ImageGenerationService
- [ ] Интегрировать с существующим FALGenerationService
- [ ] Добавить систему избранного

### Этап 3: Интерфейс (3-4 дня)
- [ ] Обновить главное меню
- [ ] Создать обработчики генерации
- [ ] Реализовать навигацию по категориям
- [ ] Добавить настройки генерации

### Этап 4: Галерея (2-3 дня)
- [ ] Создать "Моя галерея"
- [ ] Добавить поиск и фильтрацию
- [ ] Реализовать действия с изображениями
- [ ] Добавить статистику

### Этап 5: Тестирование и оптимизация (2-3 дня)
- [ ] Протестировать все сценарии
- [ ] Оптимизировать производительность
- [ ] Добавить аналитику
- [ ] Подготовить к релизу

---

## 🎯 Ключевые преимущества

### 🚀 Превосходим конкурентов
1. **Персонализация**: Шаблоны адаптируются под тип аватара
2. **Качество**: FLUX1.1 Ultra с 2K разрешением
3. **Удобство**: Меньше кликов до результата
4. **Функциональность**: Избранное, история, вариации

### 💡 Инновации
1. **Умные промпты**: Автоматическое добавление триггерных слов
2. **Адаптивные категории**: Разные шаблоны для портретных/стилевых аватаров
3. **Предиктивная загрузка**: Превью загружаются заранее
4. **Социальные функции**: Поделиться результатом

### 📊 Метрики успеха
- Увеличение конверсии в генерацию на 40%
- Снижение времени до первой генерации на 60%
- Увеличение повторных генераций на 80%
- Рост пользовательской активности на 50%

---

## ✅ Заключение

Новая система генерации изображений кардинально улучшит пользовательский опыт:

1. **Простота**: 2 клика до генерации вместо 5-7
2. **Красота**: Современный интерфейс с превью
3. **Функциональность**: Избранное, история, настройки
4. **Качество**: Лучшие модели ИИ с 2K разрешением

Система готова к реализации и превзойдет конкурентов по всем показателям! 🚀 