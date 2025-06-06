# Краткое руководство по развертыванию в продакшен

## 🎯 Цель
Перенести nginx контейнер на продакшн сервер `192.168.0.10` (Ubuntu 24)

## 📋 Подготовка продакшн сервера

### 1. Подключитесь к продакшн серверу
```bash
ssh aisha@192.168.0.10
```

### 2. Запустите настройку сервера
```bash
# Скачайте и запустите скрипт настройки
wget https://raw.githubusercontent.com/your-repo/aisha-backend/main/scripts/setup-production-server.sh
chmod +x setup-production-server.sh
sudo ./setup-production-server.sh

# Или если у вас уже есть доступ к репозиторию:
git clone https://github.com/your-repo/aisha-backend.git /opt/aisha-backend
cd /opt/aisha-backend
chmod +x scripts/setup-production-server.sh
sudo ./scripts/setup-production-server.sh
```

### 3. Перезагрузите сервер
```bash
sudo reboot
```

## 🚀 Развертывание

### Метод 1: Git Deploy (Рекомендуемый)

**На dev сервере (192.168.0.3):**

```bash
cd /opt/aisha-backend

# Убедитесь что все изменения закоммичены
git add .
git commit -m "Готов к продакшн деплою"
git push origin main

# Сделайте скрипт исполняемым
chmod +x scripts/deploy-to-production.sh

# Запустите развертывание
./scripts/deploy-to-production.sh git
```

### Метод 2: Registry Deploy (Для продвинутых)

**Если настроен Docker Registry:**

```bash
# На dev сервере
./scripts/deploy-to-production.sh registry
```

## ✅ Проверка развертывания

После развертывания проверьте:

```bash
# На продакшн сервере
ssh aisha@192.168.0.10

cd /opt/aisha-backend

# Статус контейнера
./scripts/nginx-management.sh status

# Health check
./scripts/nginx-management.sh health

# Проверка доступности
curl -I http://localhost/health
curl -Ik https://localhost:8443/health
```

**Внешняя проверка с dev сервера:**
```bash
# HTTP редирект
curl -I http://192.168.0.10/health

# HTTPS endpoint
curl -Ik https://192.168.0.10:8443/health

# Webhook endpoint
curl -Ik -X POST -H "Content-Type: application/json" \
  https://192.168.0.10:8443/api/v1/avatar/status_update
```

## 🔧 Управление в продакшене

### Основные команды
```bash
# На продакшн сервере
cd /opt/aisha-backend

# Управление через скрипт
./scripts/nginx-management.sh start     # Запуск
./scripts/nginx-management.sh stop      # Остановка  
./scripts/nginx-management.sh restart   # Перезапуск
./scripts/nginx-management.sh logs      # Логи
./scripts/nginx-management.sh metrics   # Метрики

# Управление через systemd
sudo systemctl status aisha-nginx       # Статус
sudo systemctl restart aisha-nginx      # Перезапуск
```

### Обновление
```bash
# На dev сервере - пушим изменения и деплоим
git add .
git commit -m "Обновление конфигурации"
git push origin main
./scripts/deploy-to-production.sh git

# На продакшн сервере - или просто пуллим и пересобираем
cd /opt/aisha-backend
git pull origin main
./scripts/nginx-management.sh rebuild
```

## 🆘 В случае проблем

### Проверка логов
```bash
# Логи контейнера
./scripts/nginx-management.sh logs

# Системные логи
sudo journalctl -u aisha-nginx -f

# Логи nginx
tail -f logs/nginx/nginx_access.log
tail -f logs/nginx/error.log
```

### Откат к предыдущей версии
```bash
# На продакшн сервере
cd /opt/aisha-backend
git log --oneline -10  # Найти хороший коммит
git checkout <commit_hash>
./scripts/nginx-management.sh rebuild
```

### Откат к systemd nginx
```bash
# Если Docker nginx не работает
docker-compose -f docker-compose.prod.yml stop nginx
sudo systemctl disable aisha-nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## 🎛️ Мониторинг

### Автоматический мониторинг
```bash
# Создайте cron задачу для мониторинга
crontab -e

# Добавьте строку для проверки каждые 5 минут
*/5 * * * * /opt/aisha-backend/scripts/nginx-management.sh health > /dev/null || echo "Nginx проблема" | mail -s "Aisha Nginx Alert" admin@example.com
```

### Ручной мониторинг
```bash
# Проверка ресурсов
./scripts/nginx-management.sh metrics

# Статус контейнеров
docker ps
docker stats aisha-nginx-prod

# Проверка сети
ss -tlnp | grep -E ":(80|8443)"
```

## 📊 Стратегии развертывания

### Для разных сценариев:

1. **Разработка → Продакшн**: Git Deploy
2. **Частые обновления**: Registry Deploy  
3. **Ограниченная сеть**: Image Deploy (docker save/load)
4. **Enterprise**: CI/CD Pipeline

## 🔐 Безопасность

### SSL сертификаты
```bash
# Обновление сертификатов
scp ssl_certificate/* aisha@192.168.0.10:/opt/aisha-backend/ssl_certificate/
ssh aisha@192.168.0.10 "cd /opt/aisha-backend && ./scripts/nginx-management.sh restart"
```

### Firewall
```bash
# На продакшн сервере проверьте firewall
sudo ufw status
# Должны быть открыты: 22, 80, 8443
```

---

**🎉 Готово!** Ваш nginx теперь работает в Docker контейнере на продакшн сервере с автоперезапуском и полным мониторингом. 