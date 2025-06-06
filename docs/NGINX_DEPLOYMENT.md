# Развертывание Nginx в Docker для Продакшена

## Обзор

Данная документация описывает процесс замены systemd nginx сервиса на Docker контейнер для проекта Aisha Bot в продакшене.

## Особенности конфигурации

### Порты
- **HTTP**: 80 (редирект на HTTPS)
- **HTTPS**: 8443 (как в текущей продакшн конфигурации)

### SSL сертификаты
- Сертификат: `ssl_certificate/aibots_kz_full.crt`
- Ключ: `ssl_certificate/aibots.kz.key`

### Endpoints
- `/api/v1/avatar/status_update` - webhook для FAL AI
- `/health` - health check
- `/status` - мониторинг
- `/api/v1/webhook/status` - статус webhook'ов
- `/api/*` - общие API endpoints
- Все остальные запросы возвращают 404

## Подготовка к развертыванию

### 1. Проверка окружения

```bash
# Убедитесь, что вы в корне проекта
cd /opt/aisha-backend

# Проверьте наличие файлов
ls -la docker-compose.prod.yml
ls -la ssl_certificate/aibots_kz_full.crt
ls -la ssl_certificate/aibots.kz.key
ls -la .env.docker.prod
```

### 2. Создание файла окружения

Если файл `.env.docker.prod` не существует:

```bash
cp env.docker.prod.template .env.docker.prod
# Отредактируйте файл с вашими значениями
```

### 3. Проверка SSL сертификатов

```bash
# Проверьте валидность сертификата
openssl x509 -in ssl_certificate/aibots_kz_full.crt -text -noout

# Проверьте соответствие ключа и сертификата
openssl x509 -noout -modulus -in ssl_certificate/aibots_kz_full.crt | openssl md5
openssl rsa -noout -modulus -in ssl_certificate/aibots.kz.key | openssl md5
```

## Развертывание

### Автоматическое развертывание

```bash
sudo ./scripts/deploy-nginx.sh
```

Скрипт выполнит:
1. Остановку systemd nginx сервиса
2. Создание резервной копии конфигурации
3. Проверку SSL сертификатов
4. Сборку Docker образа
5. Запуск контейнера с автоперезапуском
6. Настройку systemd сервиса для управления контейнером
7. Проверку работоспособности

### Ручное развертывание

#### 1. Остановка systemd nginx

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

#### 2. Сборка образа

```bash
docker-compose -f docker-compose.prod.yml build nginx
```

#### 3. Запуск контейнера

```bash
docker-compose -f docker-compose.prod.yml up -d nginx
```

#### 4. Проверка

```bash
docker-compose -f docker-compose.prod.yml ps nginx
curl -I http://localhost/health
curl -Ik https://localhost:8443/health
```

## Управление контейнером

### Использование скрипта управления

```bash
# Показать статус
./scripts/nginx-management.sh status

# Перезапустить
./scripts/nginx-management.sh restart

# Показать логи
./scripts/nginx-management.sh logs 100

# Health check
./scripts/nginx-management.sh health

# Пересобрать образ
./scripts/nginx-management.sh rebuild
```

### Команды Docker Compose

```bash
# Запуск
docker-compose -f docker-compose.prod.yml up -d nginx

# Остановка
docker-compose -f docker-compose.prod.yml stop nginx

# Перезапуск
docker-compose -f docker-compose.prod.yml restart nginx

# Логи
docker-compose -f docker-compose.prod.yml logs -f nginx

# Пересборка
docker-compose -f docker-compose.prod.yml build --no-cache nginx
```

### Systemd сервис

После развертывания создается systemd сервис `aisha-nginx`:

```bash
# Статус
sudo systemctl status aisha-nginx

# Запуск
sudo systemctl start aisha-nginx

# Остановка
sudo systemctl stop aisha-nginx

# Перезапуск
sudo systemctl restart aisha-nginx
```

## Мониторинг

### Health Checks

Контейнер имеет встроенный health check:
- Интервал: 15 секунд
- Таймаут: 5 секунд
- Повторы: 3
- Период запуска: 30 секунд

### Логи

Логи доступны в нескольких местах:

```bash
# Docker логи
docker-compose -f docker-compose.prod.yml logs nginx

# Логи внутри контейнера
docker exec aisha-nginx-prod tail -f /var/log/nginx/access.log
docker exec aisha-nginx-prod tail -f /var/log/nginx/error.log

# Логи на хосте
tail -f logs/nginx/nginx_access.log
tail -f logs/nginx/webhook_access.log
```

### Метрики

```bash
# Использование ресурсов
docker stats aisha-nginx-prod

# Через скрипт управления
./scripts/nginx-management.sh metrics
```

## Автоперезапуск

### Docker Restart Policy

Контейнер настроен с политикой `unless-stopped`:
- Автозапуск при перезагрузке сервера
- Перезапуск при сбоях
- Не перезапускается при ручной остановке

### Systemd Integration

Systemd сервис `aisha-nginx` обеспечивает:
- Запуск при загрузке системы
- Управление через стандартные команды systemctl
- Интеграцию с мониторингом системы

## Устранение неисправностей

### Проверка статуса

```bash
# Статус контейнера
./scripts/nginx-management.sh status

# Проверка портов
netstat -tlnp | grep -E ":(80|8443)"

# Проверка процессов nginx
docker exec aisha-nginx-prod ps aux | grep nginx
```

### Частые проблемы

#### 1. Контейнер не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.prod.yml logs nginx

# Проверьте конфигурацию
docker run --rm -v $(pwd)/docker/nginx/nginx.conf:/etc/nginx/nginx.conf nginx:1.25-alpine nginx -t
```

#### 2. SSL не работает

```bash
# Проверьте сертификаты
openssl s_client -connect localhost:8443 -servername aibots.kz

# Проверьте права на файлы
ls -la ssl_certificate/
```

#### 3. Высокое потребление ресурсов

```bash
# Посмотрите метрики
./scripts/nginx-management.sh metrics

# Настройте лимиты в docker-compose.prod.yml
```

### Откат к systemd nginx

Если нужно вернуться к systemd nginx:

```bash
# Остановите контейнер
docker-compose -f docker-compose.prod.yml stop nginx

# Отключите systemd сервис
sudo systemctl disable aisha-nginx

# Восстановите systemd nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Безопасность

### Rate Limiting

Настроены следующие лимиты:
- Webhook endpoints: 10 запросов/минуту
- API endpoints: 100 запросов/минуту
- Общие endpoints: 20 запросов/секунду

### Security Headers

Включены современные заголовки безопасности:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Referrer-Policy

### SSL Configuration

- Поддержка TLS 1.2 и 1.3
- Современные cipher suites
- OCSP stapling (если настроен)

## Backup и восстановление

### Создание backup

```bash
# Backup конфигурации
./scripts/nginx-management.sh backup

# Backup логов
tar -czf nginx-logs-$(date +%Y%m%d).tar.gz logs/nginx/
```

### Восстановление

```bash
# Восстановление из backup
cp -r backups/nginx-YYYYMMDD_HHMMSS/* docker/nginx/

# Пересборка после восстановления
./scripts/nginx-management.sh rebuild
```

## Обновление

### Обновление конфигурации

```bash
# Внесите изменения в docker/nginx/nginx.conf
# Пересоберите образ
./scripts/nginx-management.sh rebuild
```

### Обновление базового образа

```bash
# Обновите FROM в docker/nginx/Dockerfile
# Пересоберите с очисткой кеша
docker-compose -f docker-compose.prod.yml build --no-cache nginx
./scripts/nginx-management.sh restart
```

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи: `./scripts/nginx-management.sh logs`
2. Выполните health check: `./scripts/nginx-management.sh health`
3. Проверьте конфигурацию: `./scripts/nginx-management.sh config` 