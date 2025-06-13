# Исправление навигации в Imagen4

## Проблема

Кнопка "Назад" в меню Imagen4 вела обратно в меню Imagen4 вместо возврата на уровень выше (меню изображений).

## 🔧 Исправления

### Файл: `app/handlers/generation/keyboards.py`

#### 1. `build_imagen4_prompt_keyboard()`
**Было:**
```python
InlineKeyboardButton(
    text="🔙 Назад",
    callback_data="imagen4_menu"  # Возврат в то же меню!
)
```

**Стало:**
```python
InlineKeyboardButton(
    text="◀️ Назад",
    callback_data="images_menu"  # Возврат к меню изображений
)
```

#### 2. `build_imagen4_aspect_ratio_keyboard()`
**Было:**
```python
InlineKeyboardButton(
    text="🔙 Назад",
    callback_data="main_menu"  # Слишком далеко назад
)
```

**Стало:**
```python
InlineKeyboardButton(
    text="◀️ Назад",
    callback_data="images_menu"  # Правильный уровень
)
```

#### 3. `build_imagen4_menu_keyboard()`
**Было:**
```python
InlineKeyboardButton(
    text="🔙 Главное меню",
    callback_data="main_menu"
)
```

**Стало:**
```python
[
    InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="images_menu"
    ),
    InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
]
```

## 🧭 Правильная навигация

### Логика навигации:
```
Главное меню
└── 🎨 Творчество
    └── 📷 Фото (images_menu)
        └── 📝 По описанию (imagen4_generation)
            ├── Ввод промпта
            ├── Выбор размера
            └── Генерация
```

### Кнопки "Назад":
- **Из Imagen4** → `images_menu` (меню фото)
- **Из меню фото** → `ai_creativity_menu` (творчество)
- **Из творчества** → `main_menu` (главное меню)

## ✅ Результат

Теперь пользователь может:
1. Зайти в Imagen4 из меню фото
2. Вернуться назад в меню фото
3. Продолжить навигацию логично

### Унификация стиля:
- Все кнопки "Назад": **◀️ Назад**
- Главное меню: **🏠 Главное меню**
- Консистентный порядок: [Назад] [Главное меню]

## 🎯 Преимущества

1. **Логичная навигация** - пользователь возвращается туда, откуда пришел
2. **Консистентность** - единый стиль кнопок во всем приложении
3. **UX улучшение** - нет "зацикливания" в одном меню
4. **Гибкость** - есть и быстрый возврат, и переход в главное меню