# 🌐 Установка и настройка Nginx для Aisha Bot API

Данная инструкция поможет настроить nginx как reverse proxy для API сервера, обеспечив доступ к webhook через домен `aibots.kz:8443`.

## 📋 Требования

- ✅ Ubuntu/Debian сервер
- ✅ Права root (sudo)
- ✅ Домен `aibots.kz` настроен на ваш сервер
- ✅ SSL сертификаты для домена
- ✅ Запущенный API сервер на порту 8000

## 🚀 Быстрая установка

### 1. Загрузка файлов конфигурации

Убедитесь, что у вас есть файлы:
- `nginx_aisha_webhook.conf` - конфигурация nginx
- `setup_nginx.sh` - скрипт установки nginx
- `setup_firewall.sh` - скрипт настройки firewall

### 2. Подготовка SSL сертификатов

```bash
# Создайте директорию для SSL сертификатов
sudo mkdir -p /opt/aisha-backend/ssl

# Скопируйте ваши SSL сертификаты
sudo cp /path/to/your/aibots_kz.crt /opt/aisha-backend/ssl/
sudo cp /path/to/your/aibots.kz.key /opt/aisha-backend/ssl/
sudo cp /path/to/your/aibots_kz.ca-bundle /opt/aisha-backend/ssl/

# Установите правильные права доступа
sudo chmod 644 /opt/aisha-backend/ssl/*.crt
sudo chmod 600 /opt/aisha-backend/ssl/*.key
sudo chown -R aisha:aisha /opt/aisha-backend/ssl/
```

### 3. Установка nginx (если не установлен)

```bash
sudo apt update
sudo apt install -y nginx
```

### 4. Запуск скриптов установки

```bash
# Сделать скрипты исполняемыми
chmod +x setup_nginx.sh setup_firewall.sh

# Установить и настроить nginx
sudo ./setup_nginx.sh

# Настроить firewall (опционально, но рекомендуется)
sudo ./setup_firewall.sh
```

## 📝 Ручная установка

### 1. Установка конфигурации nginx

```bash
# Копирование конфигурации
sudo cp nginx_aisha_webhook.conf /etc/nginx/sites-available/aisha-webhook

# Активация конфигурации
sudo ln -sf /etc/nginx/sites-available/aisha-webhook /etc/nginx/sites-enabled/aisha-webhook

# Отключение дефолтного сайта
sudo rm -f /etc/nginx/sites-enabled/default

# Создание директорий для логов
sudo mkdir -p /var/log/aisha
sudo chown www-data:www-data /var/log/aisha
```

### 2. Проверка и перезагрузка nginx

```bash
# Проверка синтаксиса конфигурации
sudo nginx -t

# Перезагрузка nginx
sudo systemctl reload nginx

# Проверка статуса
sudo systemctl status nginx
```

## 🔧 Настройка firewall

### Автоматическая настройка

```bash
sudo ./setup_firewall.sh
```

### Ручная настройка

```bash
# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH (важно!)
sudo ufw allow 22/tcp
sudo ufw limit 22/tcp

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# API сервер только для FAL AI
sudo ufw allow from 185.199.108.0/22 to any port 8443
sudo ufw allow from 140.82.112.0/20 to any port 8443

# Локальный доступ для тестирования
sudo ufw allow from 127.0.0.1 to any port 8443
sudo ufw allow from 127.0.0.1 to any port 8000

# Блокировка прямого доступа к внутреннему API
sudo ufw deny 8000/tcp

# Активация
sudo ufw --force enable
```

## ✅ Проверка работы

### 1. Локальное тестирование

```bash
# Проверка API сервера напрямую
curl http://localhost:8000/health

# Проверка через nginx локально
curl -k https://localhost:8443/health
```

### 2. Внешнее тестирование

```bash
# Проверка через домен
curl https://aibots.kz:8443/health

# Проверка webhook endpoint
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### 3. Проверка логов

```bash
# Логи nginx
sudo tail -f /var/log/nginx/error.log

# Логи webhook
sudo tail -f /var/log/aisha/webhook_access.log
sudo tail -f /var/log/aisha/webhook_error.log

# Логи API сервера
sudo journalctl -u aisha-api -f
```

## 🔍 Диагностика проблем

### Nginx не запускается

```bash
# Проверка синтаксиса
sudo nginx -t

# Проверка статуса
sudo systemctl status nginx

# Проверка логов
sudo journalctl -u nginx -f
```

### SSL ошибки

```bash
# Проверка SSL сертификатов
sudo openssl x509 -in /opt/aisha-backend/ssl/aibots_kz.crt -text -noout

# Проверка SSL ключа
sudo openssl rsa -in /opt/aisha-backend/ssl/aibots.kz.key -check
```

### API недоступен

```bash
# Проверка API сервера
sudo systemctl status aisha-api

# Проверка портов
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8443

# Проверка firewall
sudo ufw status numbered
```

### Webhook не работает

```bash
# Проверка логов webhook
sudo tail -f /var/log/aisha/webhook_access.log
sudo tail -f /var/log/aisha/webhook_error.log

# Тестирование POST запроса
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test", "status": "completed"}' \
  -v
```

## 📊 Мониторинг

### Полезные команды

```bash
# Статус всех сервисов
sudo systemctl status nginx aisha-api

# Проверка соединений
sudo ss -tlnp | grep :8443
sudo ss -tlnp | grep :8000

# Использование ресурсов
sudo systemctl show aisha-api --property=MemoryCurrent
sudo systemctl show nginx --property=MemoryCurrent
```

### Настройка автоматического мониторинга

```bash
# Создание скрипта мониторинга
sudo tee /opt/aisha-backend/scripts/monitor_api.sh << 'EOF'
#!/bin/bash
# Проверка доступности API
if ! curl -s -f https://aibots.kz:8443/health > /dev/null; then
    echo "$(date): API недоступен" >> /var/log/aisha/monitor.log
    sudo systemctl restart aisha-api
    sudo systemctl reload nginx
fi
EOF

sudo chmod +x /opt/aisha-backend/scripts/monitor_api.sh

# Добавление в crontab (проверка каждые 5 минут)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/aisha-backend/scripts/monitor_api.sh") | crontab -
```

## 🔐 Безопасность

### Рекомендации

1. **SSL сертификаты**: Используйте только действительные SSL сертификаты
2. **Firewall**: Ограничьте доступ только для FAL AI IP адресов
3. **Логирование**: Регулярно проверяйте логи на подозрительную активность
4. **Обновления**: Регулярно обновляйте nginx и систему
5. **Мониторинг**: Настройте уведомления о недоступности сервиса

### Дополнительная защита

```bash
# Настройка fail2ban для дополнительной защиты
sudo apt install -y fail2ban

sudo tee /etc/fail2ban/jail.local << 'EOF'
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
findtime = 600
bantime = 7200
maxretry = 10
EOF

sudo systemctl restart fail2ban
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте все логи системы
2. Убедитесь, что SSL сертификаты действительны
3. Проверьте статус всех сервисов
4. Убедитесь, что firewall настроен правильно
5. Проверьте, что домен корректно указывает на ваш сервер

Удачной настройки! 🚀 