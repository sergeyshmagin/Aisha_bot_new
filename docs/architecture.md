# 🏗️ Архитектура Aisha Bot v2

## 📋 Общий обзор

Aisha Bot v2 - это современный AI-powered Telegram-бот с системой персональных аватаров, генерацией изображений и транскрибацией аудио. Проект построен на микросервисной архитектуре с использованием современных технологий.

## 🎯 Основная функциональность

### ✅ Реализовано

#### 🎭 Система AI-аватаров
- **Создание персональных моделей** через FAL AI
- **Два типа обучения**: портретные и художественные аватары
- **Автоматический пайплайн**: загрузка фото → обучение → готовая модель
- **Управление аватарами**: галерея, статусы, метаданные

#### 🖼️ Генерация изображений
- **Создание фото с аватаром** по текстовому описанию
- **Кинематографический промпт-инжиниринг** для улучшения качества
- **Анализ изображений** через GPT-4 Vision API
- **Специальные улучшения** для качества глаз и лица

#### 🔊 Транскрибация аудио
- **OpenAI Whisper API** для преобразования речи в текст
- **Smart chunking** для длинных аудиофайлов
- **Сохранение результатов** в персональной галерее

#### 💰 Система балансов
- **Кредитная система** для оплаты AI-услуг
- **Гибкая тарификация** для разных типов операций
- **История транзакций** и управление балансом

## 🏗️ Архитектура системы

```mermaid
graph TB
    subgraph "🌐 External Services"
        TG[Telegram API]
        FAL[FAL AI]
        OAI[OpenAI API]
        GPT4V[GPT-4 Vision]
    end
    
    subgraph "🤖 Bot Layer"
        TB[Telegram Bot]
        WH[Webhook Handler]
    end
    
    subgraph "🎯 Business Logic"
        AM[Avatar Manager]
        IG[Image Generator]
        AS[Audio Service]
        BS[Balance Service]
        NS[Notification Service]
    end
    
    subgraph "🔧 Core Services"
        PE[Prompt Enhancer]
        IA[Image Analyzer]
        FS[File Service]
        CS[Cache Service]
    end
    
    subgraph "💾 Data Layer"
        DB[(PostgreSQL)]
        RD[(Redis)]
        S3[(MinIO)]
    end
    
    TG <--> TB
    FAL <--> WH
    OAI <--> AS
    GPT4V <--> IA
    
    TB --> AM
    TB --> IG
    TB --> AS
    TB --> BS
    
    AM --> FAL
    AM --> NS
    IG --> PE
    IG --> IA
    
    AM --> DB
    IG --> DB
    AS --> DB
    BS --> DB
    
    FS --> S3
    CS --> RD
    
    TB --> CS
    AM --> FS
    IG --> FS
```

## 🎭 Система аватаров

### Архитектура компонентов

```mermaid
graph TB
    subgraph "📱 User Interface"
        UI[Telegram UI]
        KB[Keyboards]
        ST[State Management]
    end
    
    subgraph "🎭 Avatar System"
        AH[Avatar Handlers]
        AM[Avatar Manager]
        TS[Training Service]
        VS[Validation Service]
    end
    
    subgraph "🎨 FAL AI Integration"
        FC[FAL Client]
        FT[FAL Trainer]
        WS[Webhook Service]
        SC[Status Checker]
    end
    
    subgraph "📁 File Management"
        FM[File Manager]
        PU[Photo Upload]
        AR[Archive Creator]
        CL[Cleanup Service]
    end
    
    UI --> AH
    AH --> AM
    AM --> TS
    AM --> VS
    
    TS --> FC
    FC --> FT
    FT --> WS
    WS --> SC
    
    AM --> FM
    FM --> PU
    FM --> AR
    FM --> CL
    
    FM --> S3[(MinIO)]
    AM --> DB[(PostgreSQL)]
    WS --> RD[(Redis)]
```

### Процесс создания аватара

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant AM as Avatar Manager
    participant VS as Validation Service
    participant FM as File Manager
    participant FAL as FAL AI
    participant WH as Webhook Handler
    participant NS as Notification Service
    
    U->>B: /create_avatar
    B->>AM: start_avatar_creation()
    AM->>U: Выбор типа (портрет/стиль)
    U->>AM: Загрузка фото (10-20 шт)
    
    loop Каждое фото
        AM->>VS: validate_photo()
        VS->>VS: Проверка лица, качества, NSFW
        VS->>AM: ValidationResult
    end
    
    AM->>FM: create_training_archive()
    FM->>S3: Сохранение фото
    FM->>AM: archive_url
    
    AM->>FAL: start_training(photos, config)
    FAL->>FAL: Обучение модели (1000-4000 шагов)
    FAL->>WH: webhook(status_update)
    
    WH->>AM: update_avatar_status()
    AM->>NS: send_completion_notification()
    NS->>U: ✅ Аватар готов!
```

## 🖼️ Система генерации изображений

### Архитектура генерации

```mermaid
graph TB
    subgraph "📝 Prompt Processing"
        PI[Prompt Input]
        PE[Prompt Enhancer]
        CT[Cinema Translator]
        QE[Quality Enhancer]
    end
    
    subgraph "🖼️ Image Generation"
        IG[Image Generator]
        AC[Avatar Checker]
        GC[Generation Config]
        API[FAL Generation API]
    end
    
    subgraph "🔍 Image Analysis"
        IA[Image Analyzer]
        GPT4[GPT-4 Vision]
        PA[Prompt Analyzer]
        EE[Eye Enhancer]
    end
    
    subgraph "💾 Result Processing"
        RP[Result Processor]
        FS[File Service]
        DB[Database]
        S3[MinIO Storage]
    end
    
    PI --> PE
    PE --> CT
    CT --> QE
    QE --> IG
    
    IG --> AC
    AC --> GC
    GC --> API
    
    IG --> IA
    IA --> GPT4
    GPT4 --> PA
    PA --> EE
    
    API --> RP
    RP --> FS
    FS --> S3
    RP --> DB
```

### Процесс генерации изображения

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant IG as Image Generator
    participant PE as Prompt Enhancer
    participant AC as Avatar Checker
    participant FAL as FAL AI
    participant IA as Image Analyzer
    participant FS as File Service
    
    U->>B: Описание изображения
    B->>IG: generate_image(prompt, user_id)
    
    IG->>AC: check_main_avatar(user_id)
    AC->>IG: avatar_info
    
    IG->>PE: enhance_prompt(prompt, avatar_type)
    PE->>PE: Добавление кинематографических деталей
    PE->>PE: Улучшение качества глаз
    PE->>IG: enhanced_prompt
    
    IG->>FAL: generate(enhanced_prompt, avatar_lora)
    FAL->>IG: generated_image_url
    
    IG->>IA: analyze_image(image_url)
    IA->>GPT4V: analyze_for_improvements()
    GPT4V->>IA: analysis_result
    
    IG->>FS: save_generation_result()
    FS->>S3: Сохранение изображения
    FS->>DB: Сохранение метаданных
    
    IG->>U: 🖼️ Готовое изображение
```

## 💾 Модель данных

### Основные сущности

```mermaid
erDiagram
    User ||--o{ Avatar : creates
    User ||--o{ UserBalance : has
    User ||--o{ Transaction : makes
    User ||--o{ ImageGeneration : requests
    User ||--o{ Transcript : owns
    
    Avatar ||--o{ AvatarPhoto : contains
    Avatar ||--o{ ImageGeneration : uses
    Avatar {
        uuid id PK
        string name
        enum training_type
        enum status
        string finetune_id
        string trigger_phrase
        timestamp created_at
        timestamp training_completed_at
    }
    
    AvatarPhoto {
        uuid id PK
        uuid avatar_id FK
        string file_path
        boolean is_main
        json metadata
    }
    
    ImageGeneration {
        uuid id PK
        uuid user_id FK
        uuid avatar_id FK
        text prompt
        text enhanced_prompt
        string image_url
        json generation_config
        float cost
        timestamp created_at
    }
    
    UserBalance {
        uuid user_id PK
        decimal balance
        timestamp updated_at
    }
    
    Transaction {
        uuid id PK
        uuid user_id FK
        enum type
        decimal amount
        string description
        timestamp created_at
    }
    
    Transcript {
        uuid id PK
        uuid user_id FK
        text content
        string audio_file_path
        float duration
        float cost
        timestamp created_at
    }
```

## 🔧 Технический стек

### Backend Framework
- **Python 3.12** - Основной язык программирования
- **aiogram 3.4.1** - Telegram Bot API framework
- **FastAPI** - REST API для webhook и внешних интеграций
- **SQLAlchemy 2.0** - ORM с поддержкой async/await
- **Alembic** - Система миграций базы данных

### AI & ML Services
- **FAL AI** - Обучение персональных моделей и генерация изображений
- **OpenAI GPT-4 Vision** - Анализ изображений и улучшение промптов
- **OpenAI Whisper** - Транскрибация аудио в текст

### Data Storage
- **PostgreSQL 15+** - Основная реляционная база данных
- **Redis 7+** - Кеширование, сессии, очереди задач
- **MinIO** - S3-совместимое объектное хранилище

### Infrastructure
- **Docker & Docker Compose** - Контейнеризация и оркестрация
- **Nginx** - Reverse proxy и SSL termination
- **ffmpeg** - Обработка аудио и видео файлов

## 🌐 Сетевая архитектура

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Dev     │    │   PostgreSQL    │    │     Redis       │
│  (localhost)    │    │ (192.168.0.4)   │    │ (192.168.0.3)   │
│                 │    │                 │    │                 │
│ • Bot (polling) │◄──►│ • Port: 5432    │    │ • Port: 6379    │
│ • Scripts       │    │ • DB: aisha     │    │ • Cache & Queue │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       ▲
                                │                       │
                       ┌─────────────────┐             │
                       │     MinIO       │             │
                       │ (192.168.0.4)   │             │
                       │                 │             │
                       │ • Port: 9000    │◄────────────┘
                       │ • S3 API        │
                       │ • File Storage  │
                       └─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Production    │    │   PostgreSQL    │    │     Redis       │
│ (192.168.0.10)  │    │ (192.168.0.4)   │    │ (192.168.0.3)   │
│                 │    │                 │    │                 │
│ • Bot (webhook) │◄──►│ • Port: 5432    │    │ • Port: 6379    │
│ • API Server    │    │ • DB: aisha     │    │ • Cache & Queue │
│ • Nginx         │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         │              ┌─────────────────┐             │
         │              │     MinIO       │             │
         │              │ (192.168.0.4)   │             │
         │              │                 │             │
         └──────────────►│ • Port: 9000    │◄────────────┘
                        │ • S3 API        │
                        │ • File Storage  │
                        └─────────────────┘
```

## 🔄 Основные процессы

### Жизненный цикл аватара

1. **Создание** - Пользователь выбирает тип и загружает фото
2. **Валидация** - Проверка качества, наличия лиц, NSFW
3. **Подготовка** - Создание архива для обучения
4. **Обучение** - FAL AI обучает персональную модель (1000-4000 шагов)
5. **Завершение** - Получение LoRA модели и уведомление пользователя
6. **Использование** - Генерация изображений с обученным аватаром

### Процесс генерации изображения

1. **Ввод промпта** - Пользователь описывает желаемое изображение
2. **Проверка аватара** - Система находит основной аватар пользователя
3. **Улучшение промпта** - Добавление кинематографических деталей
4. **Генерация** - FAL AI создает изображение с аватаром
5. **Анализ результата** - GPT-4 Vision анализирует качество
6. **Сохранение** - Результат сохраняется в MinIO и БД

## 📊 Мониторинг и метрики

### Health Checks
- **Telegram API** - Проверка подключения к боту
- **PostgreSQL** - Тест подключения к БД
- **Redis** - Проверка кеша и очередей
- **MinIO** - Доступность файлового хранилища
- **FAL AI** - Валидность API ключа
- **OpenAI** - Проверка доступности API

### Ключевые метрики
- **Аватары**: создано, в обучении, завершено
- **Генерации**: количество, успешность, время выполнения
- **Транскрибации**: объем, точность, стоимость
- **Балансы**: пополнения, траты, остатки

## 🔒 Безопасность

### Аутентификация и авторизация
- **Telegram ID** как основной идентификатор
- **Автоматическая регистрация** при первом обращении
- **Проверка прав доступа** к аватарам и контенту

### Защита данных
- **Шифрование** всех API ключей в переменных окружения
- **Валидация входных данных** на всех уровнях
- **NSFW фильтрация** загружаемых изображений
- **Автоматическая очистка** временных файлов

### Rate Limiting
- **Redis-based** ограничения на количество запросов
- **Балансовая система** как естественное ограничение
- **Webhook защита** с проверкой подписи

## 🚀 Масштабирование

### Горизонтальное масштабирование
- **Stateless bot instances** - возможность запуска нескольких экземпляров
- **Redis для состояния** - общее хранилище сессий
- **MinIO clustering** - распределенное файловое хранилище

### Вертикальное масштабирование
- **Асинхронная архитектура** - эффективное использование ресурсов
- **Connection pooling** - оптимизация подключений к БД
- **Кеширование** - снижение нагрузки на основные сервисы

### Планы оптимизации
- **Background workers** - вынос тяжелых операций в отдельные процессы
- **CDN интеграция** - ускорение доставки изображений
- **Database sharding** - разделение данных по пользователям

---

**Документ актуализирован:** Июнь 2025 | **Версия:** 2.0