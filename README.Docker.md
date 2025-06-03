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

### Production (aibots.kz)
```bash
# 1. На сервере Ubuntu 24 (в /opt/aisha-backend)
sudo apt install docker.io docker-compose-plugin git -y

# 2. Клонируем/обновляем проект
cd /opt/aisha-backend
git clone <repo-url> . # или git pull

# 3. Настраиваем production переменные
cp env.docker.prod.template .env.docker.prod
nano .env.docker.prod

# 4. Автоматическое развертывание
./docker/scripts/health-check.sh
chmod +x docker/scripts/deploy-prod.sh
./docker/scripts/deploy-prod.sh

# 5. Проверяем интеграцию с nginx
curl -k https://aibots.kz:8443/health
```

## 📁 Структура

- `docker/Dockerfile.bot` - Dockerfile для Telegram бота
- `docker/Dockerfile.api` - Dockerfile для FastAPI сервера  
- `docker-compose.yml` - Development конфигурация
- `docker-compose.prod.yml` - Production конфигурация
- `docker/scripts/` - Скрипты для развертывания и проверки

## 🔧 Архитектура

- **Bot + API в контейнерах** (порт 127.0.0.1:8000 для nginx)
- **PostgreSQL, Redis, MinIO - внешние сервисы**
- **Nginx с SSL уже настроен** (`/etc/nginx/sites-enabled/aisha-webhook`)
- **Унифицированный подход dev/prod**

## 🌐 Интеграция с nginx

Ваша существующая конфигурация nginx **уже готова**! 

- ✅ Upstream: `127.0.0.1:8000` 
- ✅ SSL сертификаты: `/opt/aisha-backend/ssl/`
- ✅ Логи: `/var/log/aisha/`
- ✅ Rate limiting настроен

**Никаких изменений в nginx не требуется!**

## 📖 Подробная документация

См. [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) для детальных инструкций.

---

**💡 Рекомендация**: Используйте WSL2 для разработки на Windows! 