# 🐳 Docker Quick Start для Aisha Bot v2

**TL;DR:** Быстрый старт Docker окружения для разработки и деплоя

---

## 🏠 **Development в WSL2 (только приложения + внешние БД)**

### Требования
- WSL2 + Docker Desktop
- Git
- **🔥 Внешние сервисы уже запущены:** PostgreSQL, Redis, MinIO

### Быстрый старт
```bash
# 1. Клонирование и настройка
git clone <repository-url>
cd Aisha_bot_new
cp env.docker.template .env.docker.dev

# 2. Редактирование .env.docker.dev
# - DATABASE_HOST=localhost (или IP сервера с PostgreSQL)
# - REDIS_HOST=localhost (или IP сервера с Redis)  
# - MINIO_ENDPOINT=localhost:9000 (или IP:PORT сервера с MinIO)
# - TELEGRAM_BOT_TOKEN=your_dev_bot_token
# - OPENAI_API_KEY=sk-your_key
# - FAL_API_KEY=your_fal_key

# 3. Проверка доступности внешних сервисов
chmod +x docker/scripts/health-check.sh
./docker/scripts/health-check.sh

# 4. Запуск только приложений
docker-compose up -d

# 5. Инициализация БД (если нужно)
docker-compose exec aisha-bot alembic upgrade head
```

### Полезные команды для dev
```bash
# Логи в реальном времени
docker-compose logs -f aisha-bot

# Перезапуск с новыми изменениями
docker-compose restart aisha-bot

# Выполнение команд внутри контейнера
docker-compose exec aisha-bot bash
docker-compose exec aisha-bot python -m pytest

# Остановка всех приложений
docker-compose down

# Проверка внешних сервисов
./docker/scripts/health-check.sh
```

### Доступные эндпоинты
- **API:** http://localhost:8443/health
- **External PostgreSQL:** ваш DATABASE_HOST:5432
- **External Redis:** ваш REDIS_HOST:6379
- **External MinIO:** ваш MINIO_ENDPOINT

---

## 🌐 **Production (только приложения + nginx)**

### Унифицированная архитектура
```
Development (WSL2) + Production:
├── aisha-bot (Docker)
├── aisha-api (Docker) 
└── [nginx (Docker) - только в prod]
    │
    └── Подключение к тем же внешним БД:
        ├── PostgreSQL: ваш HOST
        ├── Redis: ваш HOST
        └── MinIO: ваш HOST
```

### Быстрое развертывание
```bash
# 1. На целевом сервере
sudo mkdir -p /opt/aisha-v2
sudo chown $USER:$USER /opt/aisha-v2
cd /opt/aisha-v2

# 2. Загрузка кода
git clone <repository-url> .

# 3. Конфигурация production
cp env.docker.template .env.docker.prod
# Редактировать с адресами ваших БД сервисов:
# DATABASE_HOST=192.168.0.10 (или другой IP)
# REDIS_HOST=192.168.0.11 (или другой IP)
# MINIO_ENDPOINT=192.168.0.12:9000 (или другой IP:PORT)

# 4. Проверка внешних сервисов
./docker/scripts/health-check.sh

# 5. Развертывание
chmod +x docker/scripts/deploy.sh
./docker/scripts/deploy.sh
```

### Управление production
```bash
# Статус systemd сервиса
sudo systemctl status aisha-bot

# Перезапуск приложения
sudo systemctl restart aisha-bot

# Логи контейнеров
docker-compose -f docker-compose.prod.yml logs -f

# Статистика ресурсов
docker stats --no-stream

# Проверка здоровья
curl -f http://localhost:8443/health  # API
curl -f http://localhost/health       # Nginx
```

---

## 🔧 **Переключение между окружениями**

### Development тестирование
```bash
# Все операции одинаковые - только приложения!
docker-compose up -d      # Запуск dev
docker-compose down       # Остановка dev
```

### Production в dev режиме
```bash
# Тестирование production конфигурации локально
cp .env.docker.prod .env.docker.test
# Изменить IP на localhost в .env.docker.test

export COMPOSE_FILE=docker-compose.prod.yml
docker-compose --env-file .env.docker.test up -d
```

### Development скрипт для production
```bash
# Запуск через скрипт развертывания в dev режиме
./docker/scripts/deploy.sh dev
```

---

## 🚨 **Troubleshooting**

### Проблемы с внешними сервисами
```bash
# Автоматическая проверка всех сервисов
./docker/scripts/health-check.sh

# Ручная проверка подключения
nc -z $DATABASE_HOST 5432   # PostgreSQL
nc -z $REDIS_HOST 6379       # Redis
nc -z $(echo $MINIO_ENDPOINT | cut -d: -f1) $(echo $MINIO_ENDPOINT | cut -d: -f2)  # MinIO

# Проверка MinIO API
curl http://$MINIO_ENDPOINT/minio/health/live

# Диагностика БД подключения
docker-compose exec aisha-bot python -c "
import asyncio
import asyncpg
import os

async def test_db():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        print('✅ PostgreSQL подключение OK')
        await conn.close()
    except Exception as e:
        print(f'❌ PostgreSQL ошибка: {e}')

asyncio.run(test_db())
"
```

### Development проблемы
```bash
# Контейнер не стартует
docker-compose logs aisha-bot

# Проблемы с переменными окружения
docker-compose exec aisha-bot env | grep -E "(DATABASE|REDIS|MINIO)"

# Очистка Docker кэша
docker system prune -f
docker builder prune -f
```

### Production проблемы
```bash
# Недоступность API
curl -v http://localhost:8443/health
docker-compose -f docker-compose.prod.yml logs aisha-api

# Проблемы с nginx
docker-compose -f docker-compose.prod.yml logs nginx
curl -v http://localhost/health

# Проблемы с systemd
sudo systemctl status aisha-bot
sudo journalctl -u aisha-bot -f
```

---

## 📋 **Checklist для нового разработчика**

### Предварительные требования
- [ ] WSL2 установлен и настроен
- [ ] Docker Desktop запущен с WSL2 integration  
- [ ] Git настроен
- [ ] **🔥 Внешние сервисы доступны:**
  - [ ] PostgreSQL запущен и доступен
  - [ ] Redis запущен и доступен
  - [ ] MinIO запущен и доступен

### Первоначальная настройка
- [ ] Репозиторий склонирован
- [ ] .env.docker.dev создан и заполнен корректными IP адресами
- [ ] `./docker/scripts/health-check.sh` прошел успешно
- [ ] `docker-compose up -d` выполнено успешно
- [ ] API отвечает на http://localhost:8443/health

### Workflow разработки
- [ ] Изменения кода автоматически перезагружаются
- [ ] Тесты выполняются в контейнере
- [ ] Логи доступны через `docker-compose logs -f`
- [ ] Подключение к внешним БД работает стабильно

### Production checklist
- [ ] Все внешние сервисы настроены и доступны
- [ ] .env.docker.prod заполнен production данными
- [ ] Скрипт развертывания работает без ошибок
- [ ] Systemd сервис настроен и запущен
- [ ] Health checks проходят успешно

---

## 🎯 **Полезные алиасы**

Добавьте в `~/.bashrc` или `~/.zshrc`:

```bash
# Docker Compose алиасы для Aisha Bot
alias dcup="docker-compose up -d"
alias dcdown="docker-compose down"
alias dclogs="docker-compose logs -f"
alias dcps="docker-compose ps"
alias dcrestart="docker-compose restart"

# Production алиасы
alias dcprod="docker-compose -f docker-compose.prod.yml"
alias aisha-status="sudo systemctl status aisha-bot"
alias aisha-logs="docker-compose -f docker-compose.prod.yml logs -f"
alias aisha-restart="sudo systemctl restart aisha-bot"

# Диагностика
alias check-services="./docker/scripts/health-check.sh"
alias check-api="curl -f http://localhost:8443/health && echo ' ✅ API OK' || echo ' ❌ API FAIL'"

# Быстрый deploy
alias deploy-dev="./docker/scripts/deploy.sh dev"
alias deploy-prod="./docker/scripts/deploy.sh"
```

---

## 🔗 **Полезные ссылки**

**📚 Документация:**
- **Полный план:** [`docs/plans/DOCKER_MIGRATION_PLAN.md`](docs/plans/DOCKER_MIGRATION_PLAN.md)
- **Архитектура:** [`docs/architecture.md`](docs/architecture.md)

**🛠️ Скрипты:**
- **Проверка сервисов:** [`docker/scripts/health-check.sh`](docker/scripts/health-check.sh)
- **Развертывание:** [`docker/scripts/deploy.sh`](docker/scripts/deploy.sh)

**⚙️ Конфигурация:**
- **Development:** [`.env.docker.dev`](.env.docker.dev)
- **Production:** [`.env.docker.prod`](.env.docker.prod)

---

**🎯 Готово к разработке!** Unified Docker архитектура обеспечивает простоту и единообразие между окружениями. 