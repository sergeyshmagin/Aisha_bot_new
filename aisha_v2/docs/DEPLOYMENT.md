# Развертывание Aisha Bot v2

## Системные требования

### Операционная система
- Ubuntu 24.04 LTS
- Python 3.11+

### Зависимости системы
```bash
# Обновление пакетов
sudo apt update
sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server

# Опционально для работы с изображениями
sudo apt install -y libpq-dev python3-dev
```

### База данных
- PostgreSQL 16+
- Redis (для кэширования и очередей)

### Хранилище файлов
- MinIO или совместимое S3 хранилище

## Подготовка окружения

1. Создание виртуального окружения:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Установка зависимостей:
```bash
pip install -r requirements.txt
```

3. Настройка переменных окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, установив необходимые значения
```

4. Настройка базы данных:
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE aisha_bot;
postgres=# CREATE USER aisha_user WITH PASSWORD 'your_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE aisha_bot TO aisha_user;
```

5. Применение миграций:
```bash
alembic upgrade head
```

## Запуск приложения

1. Запуск бота:
```bash
python -m app.main
```

2. Запуск с помощью systemd (рекомендуется для production):
```bash
sudo nano /etc/systemd/system/aisha-bot.service
```

Содержимое файла сервиса:
```ini
[Unit]
Description=Aisha Bot v2
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=aisha
Group=aisha
WorkingDirectory=/path/to/aisha_bot_v2
Environment=PYTHONPATH=/path/to/aisha_bot_v2
ExecStart=/path/to/aisha_bot_v2/venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Активация сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aisha-bot
sudo systemctl start aisha-bot
```

## Мониторинг

1. Проверка статуса:
```bash
sudo systemctl status aisha-bot
```

2. Просмотр логов:
```bash
sudo journalctl -u aisha-bot -f
```

## Обновление

1. Остановка сервиса:
```bash
sudo systemctl stop aisha-bot
```

2. Обновление кода:
```bash
git pull origin main
```

3. Обновление зависимостей:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

4. Применение миграций:
```bash
alembic upgrade head
```

5. Запуск сервиса:
```bash
sudo systemctl start aisha-bot
```
