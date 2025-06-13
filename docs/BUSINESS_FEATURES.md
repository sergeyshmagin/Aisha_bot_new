# Бизнес-функции Aisha Bot v2.1

## 🎯 Концепция

Трансформация Aisha из AI-творческого бота в **полноценного бизнес-ассистента** для управления командой и автоматизации рабочих процессов.

## 💼 Структура бизнес-раздела

### 📋 Управление задачами
**Система контроля поручений и дедлайнов**

#### ➕ Создать поручение
- Назначение задач сотрудникам
- Установка дедлайнов и приоритетов
- Описание задачи и ожидаемых результатов
- Прикрепление файлов и ссылок

#### 📊 Мои поручения  
- Список задач, которые вы выдали
- Статус выполнения каждой задачи
- Фильтрация по статусу и дедлайнам
- Возможность редактирования и отмены

#### 👥 Команда
- Обзор всех задач команды
- Загрузка каждого сотрудника
- Распределение задач по исполнителям
- Командная доска канбан

#### ⏰ Напоминания
- Автоматические уведомления о дедлайнах
- Эскалация просроченных задач
- Настройка частоты напоминаний
- Уведомления в Telegram

#### 📈 Отчеты
- Аналитика выполнения задач
- Эффективность сотрудников
- Статистика по дедлайнам
- Экспорт отчетов

### 🎤 Транскрибация
**Расшифровка деловых аудио (перенесено из AI Творчества)**

#### Бизнес-применение:
- Протоколы совещаний
- Расшифровка звонков с клиентами
- Интервью и собеседования
- Создание конспектов презентаций

#### Дополнительные функции:
- Выделение ключевых моментов
- Создание списка задач из совещания
- Поиск по расшифровкам
- Интеграция с системой поручений

### 📰 Новости и тренды
**Мониторинг информационного поля (перенесено)**

#### Бизнес-фокус:
- Отраслевые новости и тренды
- Мониторинг конкурентов
- Поиск возможностей для развития
- Анализ рыночных изменений

### 👥 Добавить в чат
**Парсинг рабочих чатов и групп**

#### 🔗 Получить ссылку-приглашение
- Генерация уникальной ссылки для добавления бота
- Настройка прав доступа в чате
- Инструкции по добавлению
- Проверка корректности подключения

#### 📋 Мои рабочие чаты
- Список всех подключенных чатов
- Статус активности парсинга
- Статистика сообщений
- Управление подписками

#### ⚙️ Настройки парсинга
- **Что отслеживать:**
  - Упоминания дедлайнов и сроков
  - Ключевые слова проектов
  - Негативные настроения
  - Запросы на помощь
- **Фильтры:**
  - Исключение системных сообщений
  - Фильтрация по участникам
  - Временные рамки анализа

#### 📊 Аналитика чатов
- **Активность:**
  - Количество сообщений по дням
  - Самые активные участники
  - Пиковые часы общения
- **Темы:**
  - Анализ обсуждаемых тем
  - Трендинг проблем
  - Sentiment analysis
- **Задачи:**
  - Автоматически выявленные поручения
  - Упоминания дедлайнов
  - Проблемы, требующие внимания

## 🛠️ Техническая реализация

### Модели данных
```python
# app/models/tasks.py
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    description = Column(Text)
    deadline = Column(DateTime)
    priority = Column(Enum("low", "medium", "high", "urgent"))
    status = Column(Enum("created", "in_progress", "review", "completed", "cancelled"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class TaskReminder(Base):
    __tablename__ = "task_reminders"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    reminder_time = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    reminder_type = Column(Enum("deadline", "progress", "overdue"))

# app/models/chats.py
class WorkChat(Base):
    __tablename__ = "work_chats"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(BigInteger, unique=True)
    chat_title = Column(String)
    is_active = Column(Boolean, default=True)
    parsing_settings = Column(JSON)
    added_at = Column(DateTime)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True)
    work_chat_id = Column(Integer, ForeignKey("work_chats.id"))
    message_id = Column(Integer)
    user_id = Column(BigInteger)
    username = Column(String)
    text = Column(Text)
    message_date = Column(DateTime)
    detected_tasks = Column(JSON)  # Найденные задачи/дедлайны
    sentiment = Column(Float)  # Анализ настроения
```

### Сервисы
```python
# app/services/task_service.py
class TaskService:
    async def create_task(self, creator_id: int, task_data: dict) -> Task
    async def assign_task(self, task_id: int, assignee_id: int) -> bool
    async def update_task_status(self, task_id: int, status: str) -> bool
    async def get_my_tasks(self, user_id: int, role: str) -> List[Task]
    async def schedule_reminder(self, task_id: int, reminder_time: datetime)
    async def send_overdue_notifications(self)

# app/services/chat_parser_service.py
class ChatParserService:
    async def add_chat(self, owner_id: int, chat_id: int, settings: dict)
    async def process_message(self, chat_id: int, message: dict)
    async def detect_tasks_in_message(self, text: str) -> List[dict]
    async def analyze_sentiment(self, text: str) -> float
    async def generate_chat_analytics(self, chat_id: int, period: str) -> dict

# app/services/reminder_service.py
class ReminderService:
    async def schedule_task_reminder(self, task: Task)
    async def send_deadline_notifications(self)
    async def escalate_overdue_tasks(self)
```

### Scheduled Jobs
```python
# app/tasks/reminders.py
@celery.task
def send_task_reminders():
    """Отправка напоминаний о задачах каждый час"""
    
@celery.task  
def process_chat_messages():
    """Обработка сообщений из рабочих чатов каждые 5 минут"""
    
@celery.task
def generate_daily_reports():
    """Генерация ежедневных отчетов по задачам"""
```

## 🔄 Интеграции

### Telegram Bot API
- Создание invite-ссылок для групповых чатов
- Парсинг сообщений в реальном времени
- Отправка уведомлений о задачах
- Работа с правами администратора

### AI Обработка
- OpenAI GPT для анализа сообщений
- Выделение задач и дедлайнов из текста
- Sentiment analysis для команды
- Автоматическая категоризация тем

### Уведомления
- Push-уведомления в Telegram
- Email-рассылки отчетов
- SMS для критичных дедлайнов
- Интеграция с календарем

## 📊 Метрики и KPI

### Эффективность команды
- Процент выполнения задач в срок
- Среднее время выполнения задач
- Количество просроченных задач
- Загрузка каждого сотрудника

### Активность в чатах
- Количество сообщений по дням
- Анализ настроения команды
- Выявленные проблемы и риски
- Автоматически созданные задачи

### ROI бизнес-функций
- Экономия времени на координацию
- Снижение количества просроченных задач
- Улучшение коммуникации в команде
- Автоматизация рутинных процессов

## 🚀 Roadmap развития

### Фаза 1 (1-2 месяца)
- Базовая система поручений
- Простые напоминания
- Подключение к групповым чатам
- Базовый парсинг сообщений

### Фаза 2 (2-3 месяца)
- AI анализ чатов
- Автоматическое создание задач
- Углубленная аналитика
- Интеграция с календарем

### Фаза 3 (3-4 месяца)
- Продвинутая отчетность
- Интеграция с CRM
- API для внешних систем
- Мобильное приложение

Этот функционал превратит Aisha в полноценного бизнес-ассистента для малого и среднего бизнеса! 