# 🔌 Настройка внешних сервисов

## 📋 Обзор

Данное руководство описывает настройку подключений к внешним сервисам для Aisha Bot:
- **PostgreSQL** - основная база данных
- **Redis** - кэш и сессии  
- **MinIO** - объектное хранилище для файлов

## 🗄️ PostgreSQL

### Требования к базе данных:
- PostgreSQL 14+
- База данных: `aisha_bot_prod`
- Пользователь с правами на создание/изменение таблиц
- Поддержка async подключений

### Создание базы и пользователя:
```sql
-- Подключитесь к PostgreSQL как суперпользователь
CREATE USER aisha_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE aisha_bot_prod OWNER aisha_user;

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE aisha_bot_prod TO aisha_user;
GRANT ALL ON SCHEMA public TO aisha_user;
```

### Настройка в .env:
```env
DATABASE_URL=postgresql+asyncpg://aisha_user:secure_password_here@your-postgres-server:5432/aisha_bot_prod
```

### Проверка подключения:
```bash
psql "postgresql://aisha_user:secure_password_here@your-postgres-server:5432/aisha_bot_prod" -c "SELECT version();"
```

## 🔴 Redis

### Требования:
- Redis 6+
- Персистентность включена (AOF или RDB)
- Доступ по паролю (рекомендуется)

### Настройка Redis:
```conf
# redis.conf
requirepass your_redis_password
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Настройка в .env:
```env
# Без пароля
REDIS_URL=redis://your-redis-server:6379/0

# С паролем
REDIS_URL=redis://:your_redis_password@your-redis-server:6379/0
```

### Проверка подключения:
```bash
redis-cli -h your-redis-server -p 6379 -a your_redis_password ping
```

## 📦 MinIO

### Требования:
- MinIO последней версии
- Bucket: `aisha-bot-storage`
- Access/Secret keys настроены
- HTTPS рекомендуется

### Создание bucket и пользователя:

#### 1. Через MinIO Console:
```bash
# Откройте веб-интерфейс MinIO
http://your-minio-server:9001

# Создайте:
# 1. Bucket: aisha-bot-storage
# 2. User: aisha-bot-user  
# 3. Policy с правами на bucket
```

#### 2. Через MC (MinIO Client):
```bash
mc alias set myminio http://your-minio-server:9000 admin password

# Создание bucket
mc mb myminio/aisha-bot-storage

# Создание пользователя
mc admin user add myminio aisha-bot-user secure_access_key

# Создание policy
cat > aisha-bot-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow", 
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::aisha-bot-storage/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::aisha-bot-storage"
    }
  ]
}
EOF

mc admin policy create myminio aisha-bot-policy aisha-bot-policy.json
mc admin policy attach myminio aisha-bot-policy --user aisha-bot-user
```

### Настройка в .env:
```env
MINIO_ENDPOINT=your-minio-server:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=aisha-bot-storage
MINIO_SECURE=true  # false для HTTP
```

### Проверка подключения:
```bash
# Через curl
curl http://your-minio-server:9000/minio/health/live

# Через MC
mc ls myminio/aisha-bot-storage
```

## 🔧 Конфигурация соединений

### Пример полного .env:
```env
# Database
DATABASE_URL=postgresql+asyncpg://aisha_user:pg_password@10.0.1.10:5432/aisha_bot_prod

# Redis
REDIS_URL=redis://:redis_password@10.0.1.11:6379/0

# MinIO
MINIO_ENDPOINT=10.0.1.12:9000
MINIO_ACCESS_KEY=aisha_access_key
MINIO_SECRET_KEY=aisha_secret_key_very_secure
MINIO_BUCKET=aisha-bot-storage
MINIO_SECURE=false

# Telegram Bot
TELEGRAM_TOKEN=1234567890:ABCDEF...

# FAL AI
FAL_API_KEY=your_fal_api_key
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
AVATAR_TEST_MODE=false

# Performance
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=20
MAX_WORKERS=4
BATCH_SIZE=50
```

## 🔐 Безопасность

### Сетевая безопасность:
```bash
# На сервере приложений разрешить исходящие подключения:
sudo ufw allow out 5432  # PostgreSQL
sudo ufw allow out 6379  # Redis  
sudo ufw allow out 9000  # MinIO

# На серверах баз данных ограничить входящие подключения:
# Только с IP app сервера
```

### Пароли и ключи:
- Используйте сильные пароли (16+ символов)
- Регулярно ротируйте access/secret keys
- Не включайте credentials в git
- Используйте переменные окружения

## 🧪 Тестирование подключений

### Автоматическая проверка:
```bash
# На app сервере запустите:
sudo -u aisha /opt/aisha_bot/scripts/test_connections.sh
```

### Ручная проверка:

#### PostgreSQL:
```bash
psql $DATABASE_URL -c "
SELECT 
  current_database() as database,
  current_user as user,
  version() as version;
"
```

#### Redis:
```bash
redis-cli -u $REDIS_URL info server
```

#### MinIO:
```bash
# Создание тестового файла
echo "test" > test.txt

# Загрузка через Python
python3 << EOF
import os
from minio import Minio

client = Minio(
    os.getenv('MINIO_ENDPOINT'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=os.getenv('MINIO_SECURE') == 'true'
)

# Загрузка тестового файла
client.fput_object('aisha-bot-storage', 'test.txt', 'test.txt')
print("✅ MinIO upload successful")

# Удаление тестового файла  
client.remove_object('aisha-bot-storage', 'test.txt')
print("✅ MinIO delete successful")
EOF

rm test.txt
```

## 🚨 Диагностика проблем

### Типичные ошибки:

#### 1. PostgreSQL connection refused
```bash
# Проверьте доступность порта
telnet postgres-server 5432

# Проверьте pg_hba.conf на сервере БД
# Должна быть строка:
# host all all your-app-server-ip/32 md5
```

#### 2. Redis NOAUTH Authentication required
```bash
# Проверьте пароль в REDIS_URL
redis-cli -h redis-server -p 6379 -a your_password ping
```

#### 3. MinIO AccessDenied
```bash
# Проверьте права пользователя
mc admin user info myminio aisha-bot-user
mc admin policy list myminio
```

### Мониторинг подключений:
```bash
# Логи подключений в приложении
sudo journalctl -fu aisha-bot | grep -i "connection\|error"

# Проверка активных соединений с БД
psql $DATABASE_URL -c "
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE usename = 'aisha_user';
"
```

## 📈 Оптимизация производительности

### PostgreSQL:
```sql
-- Настройки для app сервера в postgresql.conf
max_connections = 100
shared_buffers = 1GB  
effective_cache_size = 3GB
work_mem = 8MB
```

### Redis:
```conf
# Оптимизация для кэша
maxmemory 1gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
```

### MinIO:
```bash
# Переменные окружения для производительности
export MINIO_API_REQUESTS_MAX=1000
export MINIO_API_REQUESTS_DEADLINE=10s
```

### Пулы соединений в приложении:
```env
# Оптимальные значения для 5000+ пользователей
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
REDIS_POOL_SIZE=10
``` 