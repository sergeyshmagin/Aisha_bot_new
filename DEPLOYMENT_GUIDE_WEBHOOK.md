# 🚀 Полный деплой проекта Aisha Bot с нуля на Ubuntu 24

**Дата:** 15.01.2025  
**Цель:** Развернуть проект Aisha Bot с webhook API для FAL AI с нуля  
**Метод:** Git clone + полная настройка  

## 📋 Подготовка сервера

### 1. 🖥️ Требования к серверу:

- ✅ Ubuntu 24 LTS
- ✅ Python 3.12+
- ✅ Git
- ✅ Sudo права
- ✅ Доступ к интернету
- ✅ SSL сертификаты (для webhook)

### 2. 🔧 Установка базовых зависимостей:

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
sudo apt install -y python3 python3-pip python3-venv git curl wget nginx

# Проверяем версии
python3 --version  # Должно быть 3.12+
git --version
```

## 🚀 Полный процесс деплоя

### Шаг 1: Создание пользователя и структуры

```bash
# Создаем пользователя aisha (если не существует)
sudo useradd -m -s /bin/bash aisha
sudo usermod -aG sudo aisha

# Переключаемся на пользователя aisha
sudo su - aisha

# Создаем рабочую директорию
sudo mkdir -p /opt/aisha-backend
sudo chown -R aisha:aisha /opt/aisha-backend
cd /opt
```

### Шаг 2: Клонирование проекта

```bash
# Клонируем проект (замените на ваш репозиторий)
git clone https://github.com/your-username/aisha-bot.git aisha-backend

# Переходим в проект
cd aisha-backend

# Проверяем структуру
ls -la
```

### Шаг 3: Настройка Python окружения

```bash
# Создаем виртуальное окружение
python3 -m venv .venv

# Активируем окружение
source .venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости основного бота
pip install -r requirements.txt

# Устанавливаем зависимости API сервера
cd api_server
pip install -r requirements.txt
cd ..
```

### Шаг 4: Настройка переменных окружения

```bash
# Создаем файл .env из шаблона
cp .env.example .env

# Редактируем конфигурацию
nano .env
```

**Содержимое .env файла:**
```env
# ==================== DATABASE ====================
DATABASE_URL=postgresql+asyncpg://aisha_user:secure_password@localhost/aisha_v2

# ==================== TELEGRAM BOT ====================
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# ==================== FAL AI ====================
# ОБЯЗАТЕЛЬНО: Ваш API ключ от FAL AI
FAL_API_KEY=your_real_fal_api_key_here

# URL для webhook (должен совпадать с настройками в FAL AI)
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update

# Секрет для дополнительной безопасности (опционально)
FAL_WEBHOOK_SECRET=

# Тестовый режим (false для продакшн)
FAL_TRAINING_TEST_MODE=false

# ==================== API SERVER ====================
# Хост и порт для API сервера
API_HOST=0.0.0.0
API_PORT=8443
API_DEBUG=false
API_RELOAD=false

# ==================== SSL ====================
# Включить SSL (обязательно для webhook от FAL AI)
SSL_ENABLED=true

# Пути к SSL сертификатам
SSL_CERT_PATH=ssl/aibots_kz.crt
SSL_KEY_PATH=ssl/aibots.kz.key
SSL_CA_BUNDLE_PATH=ssl/aibots_kz.ca-bundle

# ==================== MINIO ====================
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_AVATARS=aisha-v2-avatars

# ==================== LOGGING ====================
LOG_LEVEL=INFO
LOG_DIR=logs
```

### Шаг 5: Настройка SSL сертификатов

```bash
# Создаем папку для SSL
mkdir -p ssl

# Копируем SSL сертификаты (замените на ваши файлы)
# Если у вас есть сертификаты, скопируйте их:
# sudo cp /path/to/your/cert.crt ssl/aibots_kz.crt
# sudo cp /path/to/your/key.key ssl/aibots.kz.key
# sudo cp /path/to/your/ca-bundle.crt ssl/aibots_kz.ca-bundle

# Устанавливаем правильные права
chmod 600 ssl/*
chown aisha:aisha ssl/*

# Для тестирования можно создать самоподписанный сертификат:
openssl req -x509 -newkey rsa:4096 -keyout ssl/aibots.kz.key -out ssl/aibots_kz.crt -days 365 -nodes -subj "/CN=aibots.kz"
```

### Шаг 6: Настройка базы данных PostgreSQL

```bash
# Устанавливаем PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Запускаем PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создаем базу данных и пользователя
sudo -u postgres psql << EOF
CREATE USER aisha_user WITH PASSWORD 'secure_password';
CREATE DATABASE aisha_v2 OWNER aisha_user;
GRANT ALL PRIVILEGES ON DATABASE aisha_v2 TO aisha_user;
\q
EOF

# Тестируем подключение
psql -h localhost -U aisha_user -d aisha_v2 -c "SELECT version();"
```

### Шаг 7: Создание systemd сервисов

```bash
# Создаем сервис для основного бота
sudo tee /etc/systemd/system/aisha-bot.service > /dev/null << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=aisha
Group=aisha
WorkingDirectory=/opt/aisha-backend
Environment=PATH=/opt/aisha-backend/.venv/bin
ExecStart=/opt/aisha-backend/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создаем сервис для API webhook
sudo tee /etc/systemd/system/aisha-api.service > /dev/null << EOF
[Unit]
Description=Aisha Webhook API Server
After=network.target postgresql.service

[Service]
Type=simple
User=aisha
Group=aisha
WorkingDirectory=/opt/aisha-backend/api_server
Environment=PATH=/opt/aisha-backend/.venv/bin
ExecStart=/opt/aisha-backend/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск сервисов
sudo systemctl enable aisha-bot
sudo systemctl enable aisha-api
```

### Шаг 8: Создание директорий для логов

```bash
# Создаем директории для логов
mkdir -p logs
mkdir -p api_server/logs

# Устанавливаем права
chown -R aisha:aisha logs/
chown -R aisha:aisha api_server/logs/
```

### Шаг 9: Тестирование перед запуском

```bash
# Активируем окружение
source .venv/bin/activate

# Тест конфигурации API сервера
cd api_server
python -c "from app.core.config import settings; print(f'FAL API Key: {bool(settings.effective_fal_api_key)}')"

# Тест импортов
python -c "import fal_client; print('FAL Client OK')"

# Тест запуска API (кратковременно)
timeout 10s python main.py || echo "Тест запуска API завершен"

# Возвращаемся в корень
cd ..

# Тест основного бота (если есть main.py)
# timeout 10s python main.py || echo "Тест запуска бота завершен"
```

### Шаг 10: Запуск сервисов

```bash
# Запускаем API сервис
sudo systemctl start aisha-api

# Проверяем статус
sudo systemctl status aisha-api

# Запускаем основной бот (если готов)
# sudo systemctl start aisha-bot
# sudo systemctl status aisha-bot

# Смотрим логи
sudo journalctl -u aisha-api -f --lines=20
```

### Шаг 11: Настройка файрвола (опционально)

```bash
# Настраиваем UFW
sudo ufw allow ssh
sudo ufw allow 8443/tcp  # API порт
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# Проверяем статус
sudo ufw status
```

## 🔍 Проверка работы

### Тестирование API:

```bash
# Тест health endpoint
curl http://localhost:8443/health

# Тест webhook endpoint
curl http://localhost:8443/api/v1/avatar/test_webhook

# Если SSL настроен, тест извне
curl https://aibots.kz:8443/health
curl https://aibots.kz:8443/api/v1/avatar/test_webhook
```

### Тест webhook (симуляция FAL AI):

```bash
curl -X POST http://localhost:8443/api/v1/avatar/status_update?training_type=portrait \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_12345",
    "status": "IN_PROGRESS",
    "logs": [{"message": "Training started"}]
  }'
```

## 🔧 Мониторинг и обслуживание

### Проверка логов:

```bash
# Логи systemd сервисов
sudo journalctl -u aisha-api -f
sudo journalctl -u aisha-bot -f

# Логи приложений
tail -f /opt/aisha-backend/logs/webhook.log
tail -f /opt/aisha-backend/api_server/logs/api.log

# Проверка процессов
ps aux | grep python
sudo netstat -tulpn | grep 8443
```

### Обновление проекта:

```bash
cd /opt/aisha-backend

# Останавливаем сервисы
sudo systemctl stop aisha-api
sudo systemctl stop aisha-bot

# Обновляем код
git pull origin main

# Обновляем зависимости
source .venv/bin/activate
pip install -r requirements.txt
cd api_server && pip install -r requirements.txt && cd ..

# Запускаем сервисы
sudo systemctl start aisha-api
sudo systemctl start aisha-bot
```

## 🚨 Устранение проблем

### Частые ошибки:

1. **Порт занят:**
   ```bash
   sudo netstat -tulpn | grep 8443
   sudo systemctl stop aisha-api
   ```

2. **SSL ошибки:**
   ```bash
   ls -la ssl/
   # Проверить пути в .env
   ```

3. **База данных недоступна:**
   ```bash
   sudo systemctl status postgresql
   psql -h localhost -U aisha_user -d aisha_v2 -c "SELECT 1;"
   ```

4. **Права доступа:**
   ```bash
   sudo chown -R aisha:aisha /opt/aisha-backend
   chmod 600 .env
   chmod 600 ssl/*
   ```

### Полная переустановка:

```bash
# Останавливаем сервисы
sudo systemctl stop aisha-api aisha-bot

# Удаляем проект
sudo rm -rf /opt/aisha-backend

# Начинаем заново с Шага 2
```

## ✅ Проверка готовности

После успешного деплоя должно работать:

1. ✅ `curl http://localhost:8443/health` → `{"status": "healthy"}`
2. ✅ `curl http://localhost:8443/api/v1/avatar/test_webhook` → `{"status": "ok"}`
3. ✅ `sudo systemctl status aisha-api` → `active (running)`
4. ✅ Логи без ошибок: `sudo journalctl -u aisha-api --lines=10`
5. ✅ База данных доступна: `psql -h localhost -U aisha_user -d aisha_v2 -c "SELECT 1;"`

## 🎯 Следующие шаги

После успешного деплоя:

1. **Настроить webhook URL в FAL AI** → `https://aibots.kz:8443/api/v1/avatar/status_update`
2. **Протестировать обучение аватара** через основной бот
3. **Мониторить логи** при первых webhook уведомлениях
4. **Настроить автоматические бэкапы** конфигурации и БД
5. **Настроить мониторинг** (например, через systemd или внешние сервисы)

## 📝 Структура проекта после деплоя

```
/opt/aisha-backend/
├── .env                    # Конфигурация
├── .venv/                  # Виртуальное окружение
├── requirements.txt        # Зависимости основного бота
├── main.py                 # Основной бот (если есть)
├── api_server/            # Webhook API сервер
│   ├── main.py            # Запуск API сервера
│   ├── requirements.txt   # Зависимости API
│   ├── app/               # Код приложения
│   └── logs/              # Логи API
├── ssl/                   # SSL сертификаты
├── logs/                  # Логи основного бота
└── docs/                  # Документация
```

**🎉 Проект полностью развернут и готов к работе!** 