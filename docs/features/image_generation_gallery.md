# 🎨 Фича: Галерея генерации изображений с аватарами

## 🎯 Цель

Создать интуитивный и красивый интерфейс для генерации изображений с обученными аватарами, превосходящий конкурентов по удобству и функциональности.

## 📱 Анализ конкурентов

### Что есть у конкурентов:
- ✅ Галерея примеров образов
- ✅ Группировка по стилям
- ✅ Сохраненные промпты
- ✅ Быстрая генерация по клику

### Что мы сделаем лучше:
- 🚀 **Персонализация**: Образы адаптируются под тип аватара
- 🎭 **Умные промпты**: Автодополнение с триггерными словами
- 🎨 **Качество**: Поддержка FLUX1.1 ultra с 2K разрешением
- 📊 **Аналитика**: Популярные стили и тренды
- 🔄 **Вариации**: Генерация вариаций понравившихся изображений
- 💾 **История**: Сохранение всех генераций пользователя

## 🎨 UX Flow

### 1. Вход в режим генерации
```
Главное меню → Кнопка "🎨 Создать изображение"
                        ↓
                Галерея образов (с основным аватаром)
```

### 2. Главный экран галереи
```
┌─────────────────────────────────────┐
│ 🎨 Создание с основным аватаром     │
│ 👤 Анна (Портретный стиль)          │
├─────────────────────────────────────┤
│ 🔥 Популярные стили                 │
│ [Портрет] [Арт] [Фэнтези] [Бизнес]  │
├─────────────────────────────────────┤
│ 📸 Быстрые образы                   │
│ [🏢] [🌅] [🎭] [👗] [🎨] [📚]      │
│ Офис Закат Театр Мода Арт Учеба     │
├─────────────────────────────────────┤
│ ✨ Мои любимые                      │
│ [❤️] [❤️] [❤️] [+]                 │
├─────────────────────────────────────┤
│ 📝 Свой промпт                      │
│ [Написать промпт...]                │
├─────────────────────────────────────┤
│ 🔄 Сменить аватар                   │
└─────────────────────────────────────┘
```

### 3. Выбор стиля
```
┌─────────────────────────────────────┐
│ ← 🎭 Портретные стили               │
├─────────────────────────────────────┤
│ [🏢] Деловой портрет                │
│ "professional headshot, business"   │
├─────────────────────────────────────┤
│ [🌟] Гламурный портрет              │
│ "glamour portrait, studio lighting" │
├─────────────────────────────────────┤
│ [🎨] Художественный портрет         │
│ "artistic portrait, creative"       │
├─────────────────────────────────────┤
│ [📸] Фотосессия                     │
│ "photoshoot, professional camera"   │
└─────────────────────────────────────┘
```

### 4. Процесс генерации
```
┌─────────────────────────────────────┐
│ 🎨 Создаю ваше изображение...       │
│                                     │
│ ⚡ FLUX1.1 Ultra • 2K качество      │
│ 🎭 Стиль: Деловой портрет           │
│                                     │
│ ✨ Это займет всего несколько       │
│    секунд!                          │
└─────────────────────────────────────┘
```

### 5. Результат генерации
```
┌─────────────────────────────────────┐
│ ✨ Готово!                          │
├─────────────────────────────────────┤
│                                     │
│        [ИЗОБРАЖЕНИЕ]                │
│                                     │
├─────────────────────────────────────┤
│ 💾 Сохранить  🔄 Вариация  📤 Поделиться │
│ ❤️ В избранное  🗑️ Удалить         │
├─────────────────────────────────────┤
│ 📝 "professional headshot, business" │
│ 🎯 Стиль: Деловой портрет           │
│ ⚡ Модель: FLUX1.1 Ultra            │
└─────────────────────────────────────┘
```

## 🗂️ Структура данных

### Категории образов

```python
STYLE_CATEGORIES = {
    "portrait": {
        "name": "🎭 Портреты",
        "icon": "🎭",
        "description": "Портретные стили",
        "templates": [
            {
                "id": "business",
                "name": "🏢 Деловой",
                "prompt": "professional headshot, business attire, studio lighting",
                "preview": "business_preview.jpg",
                "tags": ["профессиональный", "деловой", "офис"]
            },
            {
                "id": "glamour",
                "name": "🌟 Гламурный",
                "prompt": "glamour portrait, professional makeup, studio lighting",
                "preview": "glamour_preview.jpg",
                "tags": ["гламур", "красота", "студия"]
            },
            {
                "id": "artistic",
                "name": "🎨 Художественный",
                "prompt": "artistic portrait, creative lighting, fine art style",
                "preview": "artistic_preview.jpg",
                "tags": ["арт", "творческий", "художественный"]
            }
        ]
    },
    "lifestyle": {
        "name": "🌟 Образ жизни",
        "icon": "🌟",
        "description": "Повседневные сцены",
        "templates": [
            {
                "id": "casual",
                "name": "👕 Повседневный",
                "prompt": "casual portrait, natural lighting, relaxed pose",
                "preview": "casual_preview.jpg",
                "tags": ["повседневный", "естественный", "расслабленный"]
            },
            {
                "id": "outdoor",
                "name": "🌅 На природе",
                "prompt": "outdoor portrait, natural environment, golden hour",
                "preview": "outdoor_preview.jpg",
                "tags": ["природа", "улица", "золотой час"]
            }
        ]
    },
    "fantasy": {
        "name": "🧙‍♀️ Фэнтези",
        "icon": "🧙‍♀️",
        "description": "Фантастические образы",
        "templates": [
            {
                "id": "medieval",
                "name": "🏰 Средневековье",
                "prompt": "medieval fantasy, royal attire, castle background",
                "preview": "medieval_preview.jpg",
                "tags": ["средневековье", "фэнтези", "замок"]
            },
            {
                "id": "cyberpunk",
                "name": "🤖 Киберпанк",
                "prompt": "cyberpunk style, neon lights, futuristic setting",
                "preview": "cyberpunk_preview.jpg",
                "tags": ["киберпанк", "будущее", "неон"]
            }
        ]
    }
}
```

### Модель генерации

```python
class GenerationRequest(BaseModel):
    id: UUID
    user_id: UUID
    avatar_id: UUID
    template_id: Optional[str]
    custom_prompt: Optional[str]
    final_prompt: str
    style_category: str
    quality_preset: str = "balanced"
    aspect_ratio: str = "1:1"
    created_at: datetime
    status: GenerationStatus
    result_url: Optional[str]
    error_message: Optional[str]
    generation_time: Optional[float]
    
class UserFavoriteTemplate(BaseModel):
    user_id: UUID
    template_id: str
    added_at: datetime
    
class GenerationHistory(BaseModel):
    user_id: UUID
    avatar_id: UUID
    request_id: UUID
    template_used: Optional[str]
    prompt: str
    result_url: str
    created_at: datetime
    is_favorite: bool = False
```

## 🎨 UI Компоненты

### 1. StyleCategoryCard
```python
class StyleCategoryCard:
    """Карточка категории стилей"""
    
    def __init__(self, category: dict):
        self.category = category
        
    def render(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=f"{self.category['icon']} {self.category['name']}",
                callback_data=f"style_category:{self.category['id']}"
            )]
        ])
```

### 2. TemplateGallery
```python
class TemplateGallery:
    """Галерея шаблонов в категории"""
    
    def __init__(self, templates: List[dict]):
        self.templates = templates
        
    def render(self) -> InlineKeyboardMarkup:
        keyboard = []
        
        # По 2 шаблона в ряд
        for i in range(0, len(self.templates), 2):
            row = []
            for j in range(2):
                if i + j < len(self.templates):
                    template = self.templates[i + j]
                    row.append(InlineKeyboardButton(
                        text=f"{template['name']}",
                        callback_data=f"template:{template['id']}"
                    ))
            keyboard.append(row)
            
        return InlineKeyboardMarkup(keyboard)
```

### 3. GenerationStatus
```python
class GenerationStatus:
    """Статусные сообщения для генерации"""
    
    @staticmethod
    def get_status_message(template_name: str, model_type: str = "FLUX1.1 Ultra") -> str:
        """Возвращает статусное сообщение для генерации"""
        
        messages = [
            f"🎨 Создаю ваше изображение...\n\n⚡ {model_type} • 2K качество\n🎭 Стиль: {template_name}\n\n✨ Это займет всего несколько секунд!",
            f"🎨 Генерирую шедевр...\n\n⚡ {model_type} • Профессиональное качество\n🎭 {template_name}\n\n🚀 Уже почти готово!",
            f"✨ Создаю магию...\n\n⚡ {model_type} • Высокое разрешение\n🎭 Стиль: {template_name}\n\n🎯 Финальные штрихи!",
        ]
        
        # Возвращаем случайное сообщение для разнообразия
        import random
        return random.choice(messages)
    
    @staticmethod
    def get_custom_status_message(custom_prompt: str, model_type: str = "FLUX1.1 Ultra") -> str:
        """Статусное сообщение для кастомного промпта"""
        
        # Обрезаем промпт если он слишком длинный
        display_prompt = custom_prompt[:30] + "..." if len(custom_prompt) > 30 else custom_prompt
        
        return f"""🎨 Воплощаю вашу идею...

⚡ {model_type} • 2K качество
💭 "{display_prompt}"

✨ Создаю что-то особенное!"""
    
    @staticmethod
    def get_error_message(error_type: str = "general") -> str:
        """Сообщения об ошибках"""
        
        error_messages = {
            "no_avatar": "❌ У вас нет основного аватара\n\n🎯 Создайте аватар сначала!",
            "avatar_not_ready": "⏳ Аватар еще обучается\n\n🎯 Дождитесь завершения обучения",
            "generation_failed": "❌ Не удалось создать изображение\n\n🔄 Попробуйте еще раз",
            "rate_limit": "⏱️ Слишком много запросов\n\n🎯 Подождите немного и попробуйте снова",
            "general": "❌ Произошла ошибка\n\n🔄 Попробуйте позже"
        }
        
        return error_messages.get(error_type, error_messages["general"])
```

## 🗄️ Использование существующей инфраструктуры

### **Redis** - кэширование и сессии
```python
# Кэширование шаблонов и популярных стилей
REDIS_KEYS = {
    "templates": "generation:templates:v1",
    "popular_styles": "generation:popular:30d",
    "user_favorites": "generation:favorites:{user_id}",
    "generation_progress": "generation:progress:{request_id}",
    "user_history": "generation:history:{user_id}",
    "analytics": "generation:analytics:daily"
}

# Время жизни кэша
CACHE_TTL = {
    "templates": 3600,  # 1 час
    "popular_styles": 1800,  # 30 минут
    "user_favorites": 86400,  # 24 часа
    "generation_progress": 300,  # 5 минут
    "user_history": 3600,  # 1 час
}
```

### **PostgreSQL** - основное хранение данных
```python
# Новые таблицы для генерации
class GenerationRequest(Base):
    __tablename__ = "generation_requests"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    avatar_id: Mapped[UUID] = mapped_column(ForeignKey("avatars.id"))
    template_id: Mapped[Optional[str]]
    final_prompt: Mapped[str]
    result_url: Mapped[Optional[str]]
    status: Mapped[GenerationStatus]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
class UserFavoriteTemplate(Base):
    __tablename__ = "user_favorite_templates"
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    template_id: Mapped[str] = mapped_column(primary_key=True)
    added_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class UserSavedImage(Base):
    __tablename__ = "user_saved_images"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    generation_request_id: Mapped[UUID] = mapped_column(ForeignKey("generation_requests.id"))
    saved_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_favorite: Mapped[bool] = mapped_column(default=False)
    custom_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Пользовательское название
```

### **MinIO** - хранение сгенерированных изображений
```python
# Структура bucket'ов для генерации
MINIO_BUCKETS = {
    "generated": "aisha-v2-generated",  # Сгенерированные изображения
    "templates": "aisha-v2-templates",  # Превью шаблонов
    "temp": "aisha-v2-temp"  # Временные файлы
}

# Папки в bucket'ах
MINIO_FOLDERS = {
    "generated": {
        "daily": "generated/{date}/",  # По дням
        "user": "generated/users/{user_id}/",  # По пользователям
        "avatar": "generated/avatars/{avatar_id}/"  # По аватарам
    },
    "templates": {
        "previews": "templates/previews/",
        "categories": "templates/categories/"
    }
}
```

## 🔧 Техническая архитектура

### 1. Сервис галереи

```python
class ImageGenerationGalleryService:
    """Сервис управления галереей генерации"""
    
    def __init__(self):
        self.generation_service = FALGenerationService()
        self.template_manager = TemplateManager()
        self.redis_client = get_redis_client()
        self.storage_service = StorageService()
        
    async def get_user_main_avatar(self, user_id: UUID) -> Optional[Avatar]:
        """Получает основной аватар пользователя"""
        async with get_avatar_service() as avatar_service:
            return await avatar_service.get_main_avatar(user_id)
    
    async def get_style_categories(self, avatar_type: str) -> List[dict]:
        """Получает категории стилей для типа аватара (с кэшированием)"""
        cache_key = f"generation:categories:{avatar_type}"
        
        # Проверяем кэш
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Загружаем из конфигурации
        categories = self.template_manager.get_categories_for_type(avatar_type)
        
        # Кэшируем на 1 час
        await self.redis_client.setex(cache_key, 3600, json.dumps(categories))
        return categories
        
    async def get_templates_by_category(self, category_id: str) -> List[dict]:
        """Получает шаблоны в категории (с кэшированием)"""
        cache_key = f"generation:templates:{category_id}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        templates = self.template_manager.get_templates_by_category(category_id)
        await self.redis_client.setex(cache_key, 3600, json.dumps(templates))
        return templates
        
    async def get_user_favorites(self, user_id: UUID) -> List[dict]:
        """Получает избранные шаблоны пользователя (с кэшированием)"""
        cache_key = f"generation:favorites:{user_id}"
        
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Загружаем из БД
        async with get_db_session() as session:
            stmt = select(UserFavoriteTemplate).where(
                UserFavoriteTemplate.user_id == user_id
            )
            result = await session.execute(stmt)
            favorites = result.scalars().all()
        
        # Получаем полную информацию о шаблонах
        favorite_templates = []
        for fav in favorites:
            template = self.template_manager.get_template_by_id(fav.template_id)
            if template:
                favorite_templates.append(template)
        
        await self.redis_client.setex(cache_key, 86400, json.dumps(favorite_templates))
        return favorite_templates
        
    async def generate_from_template(
        self, 
        user_id: UUID,
        template_id: str,
        quality: str = "balanced"
    ) -> GenerationRequest:
        """Генерирует изображение по шаблону с основным аватаром"""
        
        # Получаем основной аватар
        avatar = await self.get_user_main_avatar(user_id)
        if not avatar:
            raise ValueError("У пользователя нет основного аватара")
        
        # Получаем шаблон
        template = self.template_manager.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Шаблон {template_id} не найден")
        
        # Создаем запрос в БД
        request = GenerationRequest(
            user_id=user_id,
            avatar_id=avatar.id,
            template_id=template_id,
            final_prompt=self.template_manager.build_prompt(template, avatar),
            status=GenerationStatus.PENDING
        )
        
        async with get_db_session() as session:
            session.add(request)
            await session.commit()
            await session.refresh(request)
        
        # Запускаем генерацию асинхронно
        asyncio.create_task(self._process_generation(request))
        
        return request
        
    async def generate_custom(
        self,
        user_id: UUID,
        custom_prompt: str,
        quality: str = "balanced"
    ) -> GenerationRequest:
        """Генерирует изображение по кастомному промпту с основным аватаром"""
        
        avatar = await self.get_user_main_avatar(user_id)
        if not avatar:
            raise ValueError("У пользователя нет основного аватара")
        
        # Добавляем триггерные слова к кастомному промпту
        final_prompt = self.template_manager.build_custom_prompt(custom_prompt, avatar)
        
        request = GenerationRequest(
            user_id=user_id,
            avatar_id=avatar.id,
            template_id=None,
            custom_prompt=custom_prompt,
            final_prompt=final_prompt,
            status=GenerationStatus.PENDING
        )
        
        async with get_db_session() as session:
            session.add(request)
            await session.commit()
            await session.refresh(request)
        
        asyncio.create_task(self._process_generation(request))
        return request
        
    async def _process_generation(self, request: GenerationRequest):
        """Обрабатывает генерацию изображения"""
        try:
            # Обновляем статус
            await self._update_request_status(request.id, GenerationStatus.IN_PROGRESS)
            
            # Получаем аватар
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(request.avatar_id)
            
            # Генерируем изображение
            image_url = await self.generation_service.generate_avatar_image(
                avatar=avatar,
                prompt=request.final_prompt,
                generation_config=self.generation_service.get_generation_config_presets()["balanced"]
            )
            
            if image_url:
                # Сохраняем в MinIO
                saved_url = await self._save_generated_image(request, image_url)
                
                # Обновляем запрос
                await self._update_request_result(request.id, saved_url, GenerationStatus.COMPLETED)
                
                # Обновляем статистику
                await self._update_generation_stats(request.user_id, request.avatar_id)
            else:
                await self._update_request_status(request.id, GenerationStatus.FAILED, "Не удалось сгенерировать изображение")
                
        except Exception as e:
            logger.exception(f"Ошибка генерации {request.id}: {e}")
            await self._update_request_status(request.id, GenerationStatus.FAILED, str(e))
    
    async def _save_generated_image(self, request: GenerationRequest, image_url: str) -> str:
        """Сохраняет сгенерированное изображение в MinIO"""
        
        # Скачиваем изображение
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                image_data = await response.read()
        
        # Генерируем путь для сохранения
        date_str = datetime.now().strftime("%Y/%m/%d")
        filename = f"{request.id}.jpg"
        object_path = f"generated/{date_str}/{filename}"
        
        # Сохраняем в MinIO
        await self.storage_service.upload_file(
            bucket="generated",
            object_name=object_path,
            data=image_data,
            content_type="image/jpeg"
        )
        
        # Возвращаем URL
        return await self.storage_service.get_file_url("generated", object_path)
        
    async def get_generation_history(
        self, 
        user_id: UUID, 
        limit: int = 20
    ) -> List[GenerationRequest]:
        """Получает историю генераций пользователя (с кэшированием)"""
        
        cache_key = f"generation:history:{user_id}"
        cached = await self.redis_client.get(cache_key)
        
        if cached:
            # Десериализуем из кэша
            history_data = json.loads(cached)
            return [GenerationRequest(**item) for item in history_data]
        
        # Загружаем из БД
        async with get_db_session() as session:
            stmt = (
                select(GenerationRequest)
                .where(GenerationRequest.user_id == user_id)
                .order_by(GenerationRequest.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            history = result.scalars().all()
        
        # Кэшируем на 1 час
        history_data = [
            {
                "id": str(h.id),
                "template_id": h.template_id,
                "final_prompt": h.final_prompt,
                "result_url": h.result_url,
                "status": h.status.value,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
        await self.redis_client.setex(cache_key, 3600, json.dumps(history_data))
        
        return history
```

### 2. Менеджер шаблонов

```python
class TemplateManager:
    """Менеджер шаблонов генерации"""
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> dict:
        """Загружает шаблоны из конфигурации"""
        
    def get_template_by_id(self, template_id: str) -> Optional[dict]:
        """Получает шаблон по ID"""
        
    def build_prompt(
        self, 
        template: dict, 
        avatar: Avatar,
        custom_additions: str = ""
    ) -> str:
        """Строит финальный промпт с триггерными словами"""
        
        base_prompt = template["prompt"]
        trigger = avatar.trigger_phrase or avatar.trigger_word
        
        if trigger:
            # Добавляем триггер в начало
            final_prompt = f"{trigger} {base_prompt}"
        else:
            final_prompt = base_prompt
            
        if custom_additions:
            final_prompt += f", {custom_additions}"
            
        return final_prompt
        
    def get_popular_templates(self, limit: int = 10) -> List[dict]:
        """Получает популярные шаблоны"""
        
    def search_templates(self, query: str) -> List[dict]:
        """Поиск шаблонов по запросу"""
```

### 3. Хендлеры Telegram

```python
# app/handlers/avatar/generation_gallery.py

class GenerationGalleryHandlers:
    """Хендлеры галереи генерации"""
    
    def __init__(self):
        self.gallery_service = ImageGenerationGalleryService()
        
    async def show_generation_menu(self, callback: CallbackQuery):
        """Показывает главное меню генерации с основным аватаром"""
        
        user_telegram_id = callback.from_user.id
        
        # Получаем пользователя
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await callback.answer("❌ Пользователь не найден")
                return
        
        # Получаем основной аватар
        avatar = await self.gallery_service.get_user_main_avatar(user.id)
        if not avatar:
            await callback.answer("❌ У вас нет основного аватара. Создайте аватар сначала!", show_alert=True)
            return
            
        # Получаем категории стилей
        categories = await self.gallery_service.get_style_categories(
            avatar.training_type.value
        )
        
        # Получаем избранные шаблоны
        favorites = await self.gallery_service.get_user_favorites(user.id)
        
        text = f"""
🎨 Создание с основным аватаром
👤 {avatar.name} ({avatar.training_type.value.title()} стиль)

Выберите стиль или создайте свой промпт:
        """
        
        keyboard = []
        
        # Категории стилей
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                text=f"{category['icon']} {category['name']}",
                callback_data=f"gen_category:{category['id']}"
            )])
            
        # Избранные (если есть)
        if favorites:
            keyboard.append([InlineKeyboardButton(
                text="⭐ Мои избранные",
                callback_data=f"gen_favorites"
            )])
            
        # Кастомный промпт
        keyboard.append([InlineKeyboardButton(
            text="📝 Свой промпт",
            callback_data=f"gen_custom"
        )])
        
        # История
        keyboard.append([InlineKeyboardButton(
            text="📚 Мои изображения",
            callback_data=f"gen_history"
        )])
        
        # Сменить аватар
        keyboard.append([InlineKeyboardButton(
            text="🔄 Сменить аватар",
            callback_data=f"gen_change_avatar"
        )])
        
        # Назад
        keyboard.append([InlineKeyboardButton(
            text="← Главное меню",
            callback_data="main_menu"
        )])
        
        await callback.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def show_category_templates(
        self, 
        callback: CallbackQuery, 
        avatar_id: str, 
        category_id: str
    ):
        """Показывает шаблоны в категории"""
        
        templates = await self.gallery_service.get_templates_by_category(category_id)
        
        text = f"🎭 Выберите стиль для генерации:"
        
        keyboard = []
        
        for template in templates:
            keyboard.append([InlineKeyboardButton(
                text=f"{template['name']}",
                callback_data=f"gen_template:{avatar_id}:{template['id']}"
            )])
            
        # Назад
        keyboard.append([InlineKeyboardButton(
            text="← Назад к стилям",
            callback_data=f"gen_menu:{avatar_id}"
        )])
        
        await callback.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def generate_from_template(
        self, 
        callback: CallbackQuery, 
        template_id: str
    ):
        """Запускает генерацию по шаблону"""
        
        try:
            # Получаем шаблон для отображения
            template = self.gallery_service.template_manager.get_template_by_id(template_id)
            template_name = template.get("name", "Выбранный стиль") if template else "Выбранный стиль"
            
            # Показываем статус
            status_message = GenerationStatus.get_status_message(template_name)
            await callback.message.edit_text(
                text=status_message,
                reply_markup=None
            )
            
            # Запускаем генерацию
            request = await self.gallery_service.generate_from_template(
                user_id=callback.from_user.id,
                template_id=template_id,
                quality="balanced"
            )
            
            # Ждем результат (с таймаутом)
            await self._wait_for_generation_result(callback.message, request.id)
            
        except ValueError as e:
            # Ошибки валидации (нет аватара, аватар не готов)
            if "нет основного аватара" in str(e):
                error_message = GenerationStatus.get_error_message("no_avatar")
            elif "не обучен" in str(e):
                error_message = GenerationStatus.get_error_message("avatar_not_ready")
            else:
                error_message = GenerationStatus.get_error_message("general")
                
            await callback.message.edit_text(
                text=error_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="← Назад",
                        callback_data="gen_menu"
                    )
                ]])
            )
            
        except Exception as e:
            logger.exception(f"Ошибка генерации: {e}")
            await callback.message.edit_text(
                text=GenerationStatus.get_error_message("generation_failed"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="← Назад",
                        callback_data="gen_menu"
                    )
                ]])
            )
            
    async def _wait_for_generation_result(self, message: Message, request_id: UUID):
        """Ожидает результат генерации и показывает его"""
        
        max_wait_time = 60  # Максимум 60 секунд ожидания
        check_interval = 3  # Проверяем каждые 3 секунды
        
        for _ in range(max_wait_time // check_interval):
            await asyncio.sleep(check_interval)
            
            # Проверяем статус
            request = await self.gallery_service.get_generation_request(request_id)
            
            if request.status == GenerationStatus.COMPLETED:
                await self._show_generation_result(message, request)
                return
            elif request.status == GenerationStatus.FAILED:
                await self._show_generation_error(message, request)
                return
        
        # Таймаут
        await message.edit_text(
            text=GenerationStatus.get_error_message("general"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="← Назад",
                    callback_data="gen_menu"
                )
            ]])
        )
                
    async def _show_generation_result(self, message: Message, request: GenerationRequest):
        """Показывает результат генерации"""
        
        text = f"""
✨ Изображение готово!

📝 Промпт: "{request.final_prompt}"
🎯 Стиль: {request.template_id or 'Кастомный'}
⚡ Модель: FLUX1.1 Ultra
⏱️ Время: {request.generation_time:.1f}с
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💾 Сохранить", callback_data=f"gen_save:{request.id}"),
                InlineKeyboardButton("🔄 Вариация", callback_data=f"gen_variation:{request.id}")
            ],
            [
                InlineKeyboardButton("❤️ В избранное", callback_data=f"gen_favorite:{request.id}"),
                InlineKeyboardButton("📤 Поделиться", callback_data=f"gen_share:{request.id}")
            ],
            [
                InlineKeyboardButton("← Создать еще", callback_data=f"gen_menu:{request.avatar_id}")
            ]
        ]
        
        # Отправляем изображение
        await message.reply_photo(
            photo=request.result_url,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Удаляем сообщение со статусом
        await message.delete()
        
    async def show_user_generated_images(self, callback: CallbackQuery):
        """Показывает галерею сгенерированных изображений пользователя"""
        
        user_telegram_id = callback.from_user.id
        
        # Получаем пользователя
        async with get_user_service() as user_service:
            user = await user_service.get_user_by_telegram_id(user_telegram_id)
            if not user:
                await callback.answer("❌ Пользователь не найден")
                return
        
        # Получаем историю генераций
        history = await self.gallery_service.get_generation_history(user.id, limit=50)
        
        if not history:
            await callback.message.edit_text(
                text="📚 У вас пока нет сгенерированных изображений\n\n🎨 Создайте первое изображение!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="🎨 Создать изображение",
                        callback_data="gen_menu"
                    )
                ]])
            )
            return
        
        # Группируем по дням
        grouped_history = self._group_history_by_date(history)
        
        # Показываем первую страницу
        await self._show_history_page(callback, grouped_history, page=0)
    
    def _group_history_by_date(self, history: List[GenerationRequest]) -> Dict[str, List[GenerationRequest]]:
        """Группирует историю по датам"""
        from collections import defaultdict
        
        grouped = defaultdict(list)
        for item in history:
            date_key = item.created_at.strftime("%Y-%m-%d")
            grouped[date_key].append(item)
        
        return dict(grouped)
    
    async def _show_history_page(self, callback: CallbackQuery, grouped_history: Dict, page: int = 0):
        """Показывает страницу истории"""
        
        dates = list(grouped_history.keys())
        items_per_page = 10
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        
        if start_idx >= len(dates):
            await callback.answer("📄 Больше нет изображений")
            return
        
        current_dates = dates[start_idx:end_idx]
        
        text = "📚 Ваши сгенерированные изображения:\n\n"
        keyboard = []
        
        for date_key in current_dates:
            items = grouped_history[date_key]
            date_formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%d.%m.%Y")
            
            text += f"📅 {date_formatted} ({len(items)} шт.)\n"
            
            # Добавляем кнопки для каждого изображения дня
            day_buttons = []
            for i, item in enumerate(items[:6]):  # Максимум 6 на день
                emoji = "🎭" if item.template_id else "💭"
                day_buttons.append(InlineKeyboardButton(
                    text=f"{emoji}{i+1}",
                    callback_data=f"gen_view:{item.id}"
                ))
            
            # Разбиваем по 3 кнопки в ряд
            for i in range(0, len(day_buttons), 3):
                keyboard.append(day_buttons[i:i+3])
            
            if len(items) > 6:
                keyboard.append([InlineKeyboardButton(
                    text=f"📅 Все за {date_formatted} ({len(items)})",
                    callback_data=f"gen_day:{date_key}"
                )])
            
            text += "\n"
        
        # Навигация
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"gen_history_page:{page-1}"
            ))
        
        if end_idx < len(dates):
            nav_buttons.append(InlineKeyboardButton(
                text="➡️ Далее",
                callback_data=f"gen_history_page:{page+1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Кнопки действий
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ Очистить историю",
                callback_data="gen_clear_history"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="gen_stats"
            )
        ])
        
        keyboard.append([InlineKeyboardButton(
            text="← Назад к генерации",
            callback_data="gen_menu"
        )])
        
        await callback.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_generated_image_details(self, callback: CallbackQuery, request_id: str):
        """Показывает детали сгенерированного изображения"""
        
        try:
            request = await self.gallery_service.get_generation_request(UUID(request_id))
            if not request:
                await callback.answer("❌ Изображение не найдено")
                return
            
            # Проверяем что это изображение пользователя
            user_telegram_id = callback.from_user.id
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user or user.id != request.user_id:
                    await callback.answer("❌ Доступ запрещен")
                    return
            
            # Формируем информацию
            created_date = request.created_at.strftime("%d.%m.%Y в %H:%M")
            template_name = "Кастомный промпт" if not request.template_id else "Шаблон"
            
            text = f"""
🖼️ Детали изображения

📅 Создано: {created_date}
🎭 Тип: {template_name}
💭 Промпт: "{request.final_prompt}"

⚡ Модель: FLUX1.1 Ultra
🎯 Статус: {"✅ Готово" if request.status == GenerationStatus.COMPLETED else "❌ Ошибка"}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📤 Поделиться", callback_data=f"gen_share:{request_id}"),
                    InlineKeyboardButton("🔄 Вариация", callback_data=f"gen_variation:{request_id}")
                ],
                [
                    InlineKeyboardButton("🗑️ Удалить", callback_data=f"gen_delete:{request_id}"),
                    InlineKeyboardButton("💾 Скачать", callback_data=f"gen_download:{request_id}")
                ],
                [
                    InlineKeyboardButton("← К галерее", callback_data="gen_history")
                ]
            ]
            
            # Отправляем изображение с деталями
            await callback.message.reply_photo(
                photo=request.result_url,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.exception(f"Ошибка показа деталей изображения: {e}")
            await callback.answer("❌ Произошла ошибка")
        
    async def handle_custom_prompt_generation(self, message: Message, custom_prompt: str):
        """Обрабатывает генерацию по кастомному промпту"""
        
        try:
            # Показываем статус
            status_message = GenerationStatus.get_custom_status_message(custom_prompt)
            status_msg = await message.reply(status_message)
            
            # Запускаем генерацию
            request = await self.gallery_service.generate_custom(
                user_id=message.from_user.id,
                custom_prompt=custom_prompt,
                quality="balanced"
            )
            
            # Ждем результат
            await self._wait_for_generation_result(status_msg, request.id)
            
        except ValueError as e:
            if "нет основного аватара" in str(e):
                error_message = GenerationStatus.get_error_message("no_avatar")
            elif "не обучен" in str(e):
                error_message = GenerationStatus.get_error_message("avatar_not_ready")
            else:
                error_message = GenerationStatus.get_error_message("general")
                
            await message.reply(
                text=error_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="🎨 Галерея стилей",
                        callback_data="gen_menu"
                    )
                ]])
            )
            
        except Exception as e:
            logger.exception(f"Ошибка кастомной генерации: {e}")
            await message.reply(
                text=GenerationStatus.get_error_message("generation_failed"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="🎨 Галерея стилей", 
                        callback_data="gen_menu"
                    )
                ]])
            )
```

## 📊 Аналитика и метрики

### Отслеживаемые метрики

```python
class GenerationAnalytics:
    """Аналитика генераций"""
    
    async def track_generation(self, request: GenerationRequest):
        """Отслеживает генерацию"""
        
    async def get_popular_templates(self, period_days: int = 30) -> List[dict]:
        """Получает популярные шаблоны за период"""
        
    async def get_user_preferences(self, user_id: UUID) -> dict:
        """Анализирует предпочтения пользователя"""
        
    async def get_generation_stats(self) -> dict:
        """Получает общую статистику генераций"""
        return {
            "total_generations": 1250,
            "avg_generation_time": 18.5,
            "popular_styles": ["business", "glamour", "artistic"],
            "success_rate": 0.95,
            "user_satisfaction": 4.7
        }
```

## 🚀 План реализации

### Этап 1: Базовая функциональность (1-2 дня)
- ✅ Создание моделей данных в PostgreSQL
- ✅ Настройка Redis кэширования
- ✅ Интеграция с MinIO для хранения изображений
- ✅ Базовый сервис генерации с основным аватаром
- ✅ Простые хендлеры Telegram
- ✅ Интеграция с FALGenerationService

### Этап 2: UI и UX (2-3 дня)
- 🎨 Создание галереи шаблонов
- 📱 Красивые карточки стилей
- 🔄 Индикатор прогресса
- ⭐ Система избранного

### Этап 3: Продвинутые фичи (2-3 дня)
- 📚 Галерея "Мои изображения" с группировкой по датам
- 💾 Система сохранения избранных изображений
- 🔄 Генерация вариаций существующих изображений
- 📤 Система шаринга и скачивания
- 🗑️ Управление историей (удаление, очистка)
- 🎯 Персонализация рекомендаций

### Этап 4: Аналитика и оптимизация (1-2 дня)
- 📊 Система метрик
- 🚀 Оптимизация производительности
- 🧪 A/B тестирование шаблонов
- 📈 Дашборд аналитики

## 🎯 Ключевые преимущества

### Для пользователей:
- 🚀 **Быстрота**: Генерация в 1 клик
- 🎨 **Качество**: FLUX1.1 Ultra с 2K разрешением
- 💡 **Вдохновение**: Готовые стили и образы
- 📱 **Удобство**: Интуитивный интерфейс
- ❤️ **Персонализация**: Избранное и рекомендации

### Для бизнеса:
- 📈 **Вовлеченность**: Увеличение времени в боте
- 💰 **Монетизация**: Премиум стили и качество
- 📊 **Данные**: Аналитика предпочтений пользователей
- 🎯 **Удержание**: Постоянное обновление контента

## 🔮 Будущие улучшения

### Версия 2.0:
- 🤖 **ИИ-рекомендации**: Персональные стили на основе истории
- 🎭 **Эмоциональные стили**: Генерация по настроению
- 👥 **Социальные фичи**: Галерея сообщества, лайки, комментарии
- 🎮 **Геймификация**: Достижения, коллекции стилей

### Версия 3.0:
- 🎬 **Видео-аватары**: Анимированные изображения
- 🌍 **AR интеграция**: Примерка образов в дополненной реальности
- 🎨 **Кастомные стили**: Обучение персональных стилей
- 🤝 **Коллаборации**: Совместное создание образов

---

**Готовы начать реализацию? Этот план создаст лучший в классе интерфейс для генерации изображений! 🚀** 