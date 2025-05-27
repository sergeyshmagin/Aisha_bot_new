# 🔧 Исправление архитектуры портов Aisha Bot

## 🚨 Проблема

**Конфликт портов:** И API сервер, и Nginx пытались использовать порт 8443.

### Было (неправильно):
```
API сервер: 8443 ← КОНФЛИКТ
Nginx: 8443      ← КОНФЛИКТ
```

### Стало (правильно):
```
API сервер: 8000 (локально)
Nginx: 8443 (SSL, внешний доступ) → проксирует на localhost:8000
```

## 🔧 Исправления

### 1. Изменен `launch_webhook_api.py`
```python
# Было:
port=8443

# Стало:
port=8000  # API сервер на 8000, Nginx на 8443
```

### 2. Архитектура сервисов

| Сервис | Порт | Доступ | Назначение |
|--------|------|--------|------------|
| **API сервер** | 8000 | Локальный | FastAPI приложение |
| **Nginx** | 8443 | Внешний | SSL терминация + reverse proxy |

### 3. Поток запросов
```
FAL AI webhook → https://aibots.kz:8443 → Nginx (SSL) → http://localhost:8000 → API сервер
```

## 🚀 Применение исправлений

### Автоматическое исправление:
```bash
# Запустить скрипт исправления
chmod +x fix_port_architecture.sh
./fix_port_architecture.sh
```

### Ручное исправление:
```bash
# 1. Остановить сервисы
sudo systemctl stop aisha-api.service nginx.service

# 2. Очистить порты
sudo pkill -f "port.*8443"
sudo pkill -f "port.*8000"

# 3. Запустить API на 8000
sudo systemctl start aisha-api.service

# 4. Запустить Nginx на 8443
sudo systemctl start nginx.service
```

## ✅ Проверка работы

### 1. Проверка портов:
```bash
# API сервер должен слушать 8000
sudo lsof -i :8000
# Ожидается: python (aisha-api.service)

# Nginx должен слушать 8443
sudo lsof -i :8443
# Ожидается: nginx
```

### 2. Проверка API:
```bash
# Прямо к API серверу
curl http://localhost:8000/health
# Ожидается: {"status":"healthy",...}

# Через Nginx (HTTP)
curl http://localhost:8443/health
# Ожидается: {"status":"healthy",...}

# Через Nginx (HTTPS)
curl -k https://localhost:8443/health
# Ожидается: {"status":"healthy",...}
```

### 3. Проверка webhook:
```bash
# Тест webhook endpoint
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test", "status": "completed"}' \
  -k
```

## 📊 Статус сервисов

```bash
# Проверка статуса
sudo systemctl status aisha-api.service
sudo systemctl status nginx.service

# Логи
sudo journalctl -u aisha-api.service -f
sudo journalctl -u nginx.service -f
```

## 🔗 Обновленные URL

| Назначение | URL | Описание |
|------------|-----|----------|
| **Health check (API)** | `http://localhost:8000/health` | Прямо к API |
| **Health check (Nginx)** | `https://aibots.kz:8443/health` | Через SSL |
| **Webhook endpoint** | `https://aibots.kz:8443/api/v1/avatar/status_update` | FAL AI webhook |

## 🚨 Важно

После исправления архитектуры:
1. **Webhook URL в FAL AI** остается тем же: `https://aibots.kz:8443/api/v1/avatar/status_update`
2. **Внешний доступ** только через Nginx (порт 8443)
3. **API сервер** доступен только локально (порт 8000)
4. **SSL сертификаты** обрабатывает только Nginx

---

**✅ После применения исправлений конфликт портов будет устранен!** 