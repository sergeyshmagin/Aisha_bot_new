# 🐳 Aisha Bot v2 - Docker Deployment

## 🚀 Быстрый старт

### Development
```bash
# 1. Копируем переменные окружения
cp env.docker.dev.template .env.docker.dev

# 2. Редактируем .env.docker.dev с вашими настройками
nano .env.docker.dev

# 3. Проверяем доступность внешних сервисов
./docker/scripts/health-check.sh

# 4. Запускаем
docker-compose up -d

# 5. Смотрим логи
docker-compose logs -f
```

### Production
```bash
# 1. На сервере Ubuntu 24
sudo apt install docker.io docker-compose-plugin git -y

# 2. Клонируем проект
git clone <repo-url> /opt/aisha-v2 && cd /opt/aisha-v2

# 3. Настраиваем production переменные
cp env.docker.dev.template .env.docker.prod
nano .env.docker.prod

# 4. Проверяем сервисы и запускаем
./docker/scripts/health-check.sh
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 Структура

- `docker/Dockerfile.bot` - Dockerfile для Telegram бота
- `docker/Dockerfile.api` - Dockerfile для FastAPI сервера  
- `docker-compose.yml` - Development конфигурация
- `docker-compose.prod.yml` - Production конфигурация
- `docker/scripts/health-check.sh` - Проверка внешних сервисов

## 🔧 Архитектура

- **Bot + API в контейнерах**
- **PostgreSQL, Redis, MinIO - внешние сервисы**
- **Унифицированный подход dev/prod**

## 📖 Подробная документация

См. [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) для детальных инструкций.

---

**💡 Рекомендация**: Используйте WSL2 для разработки на Windows! 