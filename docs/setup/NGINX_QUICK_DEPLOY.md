# Быстрое развертывание Nginx в Docker

## Подготовка

1. **Убедитесь, что вы в корне проекта**:
   ```bash
   cd /opt/aisha-backend
   ```

2. **Проверьте файлы**:
   ```bash
   ls -la docker-compose.prod.yml
   ls -la ssl_certificate/aibots_kz_full.crt
   ls -la ssl_certificate/aibots.kz.key
   ls -la .env.docker.prod
   ```

3. **Сделайте скрипты исполняемыми**:
   ```bash
   chmod +x scripts/deploy-nginx.sh
   chmod +x scripts/nginx-management.sh
   chmod +x docker/nginx/healthcheck.sh
   ```

## Автоматическое развертывание

```bash
sudo ./scripts/deploy-nginx.sh
```

Скрипт автоматически:
- Остановит systemd nginx
- Создаст backup конфигурации
- Соберет Docker образ
- Запустит контейнер с автоперезапуском
- Настроит systemd сервис для управления
- Проверит работоспособность

## Проверка после развертывания

```bash
# Статус контейнера
./scripts/nginx-management.sh status

# Health check
./scripts/nginx-management.sh health

# Проверка HTTP
curl -I http://localhost/health

# Проверка HTTPS
curl -Ik https://localhost:8443/health
```

## Управление

```bash
# Основные команды
./scripts/nginx-management.sh start     # Запуск
./scripts/nginx-management.sh stop      # Остановка
./scripts/nginx-management.sh restart   # Перезапуск
./scripts/nginx-management.sh rebuild   # Пересборка образа

# Мониторинг
./scripts/nginx-management.sh logs      # Логи
./scripts/nginx-management.sh metrics   # Метрики
./scripts/nginx-management.sh health    # Проверка здоровья

# Через systemd
sudo systemctl status aisha-nginx       # Статус
sudo systemctl restart aisha-nginx      # Перезапуск
```

## Особенности конфигурации

- **Порт HTTP**: 80 (редирект на HTTPS)
- **Порт HTTPS**: 8443 (как в текущей продакшн конфигурации)
- **Автоперезапуск**: `unless-stopped`
- **Лимиты памяти**: 256M
- **Health checks**: каждые 15 секунд

## В случае проблем

1. **Проверьте логи**:
   ```bash
   ./scripts/nginx-management.sh logs
   ```

2. **Проверьте конфигурацию**:
   ```bash
   ./scripts/nginx-management.sh config
   ```

3. **Откат к systemd nginx**:
   ```bash
   docker-compose -f docker-compose.prod.yml stop nginx
   sudo systemctl disable aisha-nginx
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

Подробная документация доступна в `docs/NGINX_DEPLOYMENT.md` 