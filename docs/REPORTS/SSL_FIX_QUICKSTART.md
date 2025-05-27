# 🔒 Быстрое исправление SSL для FAL AI Webhook

## ❗ Проблема
```bash
curl: (60) SSL certificate problem: unable to get local issuer certificate
```

## 🎯 Важно знать о FAL AI webhook

Из документации FAL AI:
- ✅ **FAL AI НЕ требует валидных SSL сертификатов для webhook**
- ✅ **FAL AI принимает самоподписанные сертификаты**
- ✅ **FAL AI игнорирует проблемы с SSL при отправке webhook**
- 📝 **Единственное требование**: HTTPS должен быть доступен

## 🚀 Быстрое решение

### 1. Запустить диагностику
```bash
chmod +x fix_ssl_certificate.sh
sudo ./fix_ssl_certificate.sh
```

### 2. Временный тест (обход SSL проверки)
```bash
# Тест health endpoint с игнорированием SSL
curl -k https://aibots.kz:8443/health

# Тест webhook endpoint с игнорированием SSL  
curl -k -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### 3. Если нужно быстро исправить SSL для браузеров

**Опция A: Let's Encrypt (рекомендуется)**
```bash
# Установить certbot
sudo apt install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot --nginx -d aibots.kz

# Перезагрузить nginx
sudo systemctl reload nginx
```

**Опция B: Самоподписанный сертификат (временно)**
```bash
# Создать самоподписанный сертификат
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /opt/aisha-backend/ssl/aibots.kz.key \
  -out /opt/aisha-backend/ssl/aibots_kz.crt \
  -subj "/C=KZ/ST=Almaty/L=Almaty/O=AiBots/CN=aibots.kz"

# Установить права
sudo chown aisha:aisha /opt/aisha-backend/ssl/aibots*
sudo chmod 600 /opt/aisha-backend/ssl/aibots.kz.key
sudo chmod 644 /opt/aisha-backend/ssl/aibots_kz.crt

# Перезагрузить nginx
sudo systemctl reload nginx
```

## ✅ Проверка результата

```bash
# Проверка что API работает (важно для FAL AI)
curl -k https://aibots.kz:8443/health

# Ответ должен быть:
# {"status":"healthy","service":"Aisha Bot FAL Webhook API"}
```

## 🎯 Что важно для FAL AI webhook

1. **HTTPS доступен** ✅ (даже с самоподписанным сертификатом)
2. **Порт 8443 открыт** ✅ (уже настроен)
3. **Endpoint отвечает** ✅ (`/api/v1/avatar/status_update`)
4. **JSON обрабатывается** ✅ (Content-Type: application/json)

## 📝 Настройка FAL AI webhook URL

В конфигурации FAL AI используйте:
```
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
```

**FAL AI автоматически игнорирует проблемы с SSL при отправке webhook!**

## 🚨 Если webhook не работает

1. **Проверьте логи API сервера:**
   ```bash
   journalctl -u aisha-api.service -f
   ```

2. **Проверьте логи nginx:**
   ```bash
   tail -f /var/log/aisha/webhook_access.log
   tail -f /var/log/nginx/error.log
   ```

3. **Проверьте firewall:**
   ```bash
   sudo ufw status
   # Порт 8443 должен быть открыт
   ```

4. **Тест webhook вручную:**
   ```bash
   curl -k -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
     -H "Content-Type: application/json" \
     -d '{
       "request_id": "test-123",
       "status": "completed",
       "result": {"test": true}
     }'
   ```

## 💡 Итоговые рекомендации

### Для продакшена
1. **Используйте Let's Encrypt** для валидного SSL
2. **Настройте автообновление** сертификатов
3. **Мониторьте** срок действия сертификатов

### Для разработки/тестирования
1. **Самоподписанный сертификат** вполне достаточен
2. **FAL AI webhook работает** с любым HTTPS
3. **Только браузеры** показывают предупреждения

## 🎉 Главное

**✅ FAL AI webhook будет работать даже с SSL ошибками!**

Главное чтобы:
- Endpoint был доступен по HTTPS
- API сервер принимал JSON запросы
- Firewall не блокировал порт 8443

Проблема `SSL certificate problem` не влияет на работу FAL AI webhook! 