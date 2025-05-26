# Отчёт о Legacy функциях и дублирующемся коде

## 🎯 Цель
Найти и пометить все дублирующиеся и устаревшие Legacy функции в проекте для последующего удаления.

## 📋 Найденные Legacy функции

### 1. **Avatar Service** 

#### 🔴 `app/services/avatar_db.py`
- **Строка 193:** `delete_avatar()` - LEGACY алиас для `delete_avatar_completely`
  ```python
  # LEGACY: Устаревший метод для обратной совместимости
  # TODO: Удалить после миграции всех вызовов на delete_avatar_completely
  async def delete_avatar(self, avatar_id: UUID) -> bool:
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Заменить все вызовы на `delete_avatar_completely`

### 2. **Avatar Handlers**

#### 🔴 `app/handlers/avatar/__init__.py`
- **Строка 23:** `AvatarHandler` класс - LEGACY заглушка для тестов
  ```python
  # =================== LEGACY CODE - ПОМЕТИТЬ К УДАЛЕНИЮ ===================
  # LEGACY: Заглушка для совместимости с тестами (для старого AvatarHandler)
  class AvatarHandler:
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Рефакторить тесты на новую архитектуру роутеров

- **Строка 39:** `process_avatar_name()` - LEGACY обработчик имени
  ```python
  # LEGACY: Устаревший метод - используйте обработчики в create.py вместо этого
  async def process_avatar_name(self, message, state):
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Использовать обработчики из `create.py`

- **Строка 57:** `register_avatar_handlers()` - LEGACY функция регистрации
  ```python
  # LEGACY: Функция для регистрации обработчиков (для совместимости с main.py)
  async def register_avatar_handlers():
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Перейти на роутеры

### 3. **Database Models**

#### 🔴 `app/database/models.py`
- **Строка 198:** Legacy поля в `Avatar` модели
  ```python
  # =================== LEGACY FIELDS - ПОМЕТИТЬ К УДАЛЕНИЮ ===================
  # LEGACY: Поля для совместимости со старой системой
  is_draft: Mapped[bool] = mapped_column(Boolean, default=True)  # LEGACY: используйте status вместо этого
  photo_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # LEGACY: не используется в новой системе
  preview_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # LEGACY: не используется в новой системе
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Создать миграцию для удаления после проверки использования

- **Строка 242:** Legacy поле в `AvatarPhoto` модели
  ```python
  # LEGACY: Поле для совместимости
  order: Mapped[int] = mapped_column(Integer, default=0)  # LEGACY: используйте upload_order вместо этого
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Заменить на `upload_order`

### 4. **Transcript Services**

#### 🔴 `app/services/transcript.py`
- **Строка 157:** `get_user_transcripts()` - LEGACY метод
  ```python
  # LEGACY: Устаревший метод для обратной совместимости
  # TODO: Удалить после полной миграции на list_transcripts
  async def get_user_transcripts(self, user_id: Union[int, str, UUID]) -> List[Dict]:
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Использовать `list_transcripts`

#### 🔴 `app/database/repositories/transcript.py`
- **Строка 26:** `get_user_transcripts()` - LEGACY репозиторий
  ```python
  # LEGACY: Устаревший метод для совместимости
  # TODO: Удалить после миграции на новую систему транскриптов
  async def get_user_transcripts(self, user_id: Union[int, str, UUID], limit: int = 10, offset: int = 0) -> List[UserTranscript]:
  ```
  - **Статус:** ✅ ПОМЕЧЕНО как LEGACY
  - **Рекомендация:** Рефакторить на новую систему

### 5. **Исправленные повреждения**

#### ✅ `app/keyboards/avatar_clean.py`
- **Строка 47:** `get_training_type_keyboard()` - исправлено повреждение из-за Legacy очистки
  ```python
  def get_training_type_keyboard() -> InlineKeyboardMarkup:
      """Клавиатура выбора типа обучения (ИСПРАВЛЕНО после Legacy повреждения)"""
  ```
  - **Статус:** ✅ ИСПРАВЛЕНО
  - **Проблема:** Функция была повреждена при некорректном применении Legacy изменений

## 📊 Статистика

### 🔴 Legacy функции к удалению:
- **Avatar Service:** 1 метод
- **Avatar Handlers:** 3 функции/класса  
- **Database Models:** 4 поля
- **Transcript Services:** 2 метода
- **ИТОГО:** 10 Legacy элементов

### ✅ Исправлено:
- **Поврежденные файлы:** 1 функция
- **Синтаксические ошибки:** исправлены

## 🎯 План дальнейших действий

### 🔥 Приоритет 1 (КРИТИЧНО):
1. **Заменить вызовы `delete_avatar` → `delete_avatar_completely`**
2. **Рефакторить тесты с `AvatarHandler` на роутеры**

### 🔥 Приоритет 2 (ВАЖНО):
3. **Мигрировать Legacy поля в БД** (создать миграцию Alembic)
4. **Заменить `order` → `upload_order` в коде**
5. **Рефакторить транскрипты на новую систему**

### 🔥 Приоритет 3 (ПЛАНОВО):
6. **Удалить Legacy поля из моделей БД** (после миграции)
7. **Очистить Legacy комментарии и классы**
8. **Обновить документацию**

## ⚠️ Предупреждения

1. **НЕ УДАЛЯТЬ** Legacy поля из БД без миграции - **ПОТЕРЯ ДАННЫХ!**
2. **НЕ УДАЛЯТЬ** `AvatarHandler` до рефакторинга тестов
3. **ПРОВЕРИТЬ** все вызовы Legacy методов перед удалением

## ✅ Результат

🎯 **Все Legacy функции найдены и помечены**  
🔧 **Повреждения от Legacy очистки исправлены**  
📋 **План действий составлен**

Проект готов к поэтапному удалению Legacy кода без потери функциональности. 