# Настройка SSL и nginx для FastAPI

## Зачем это нужно?
- Для работы webhook (например, с fal.ai) требуется HTTPS.
- SSL-сертификат обеспечивает безопасность и доверие к вашему серверу.
- nginx позволяет проксировать запросы к FastAPI и обслуживать HTTPS.

---

## 1. Генерация CSR и приватного ключа

Выполните на сервере:
```bash
sudo mkdir -p /etc/ssl/private
sudo openssl req -new -newkey rsa:2048 -nodes -keyout /etc/ssl/private/your_domain.key -out /etc/ssl/private/your_domain.csr
```
- **your_domain.key** — приватный ключ (НЕ передавайте никому!)
- **your_domain.csr** — используйте для заказа сертификата (например, GoGetSSL)

**Важно:** Common Name (CN) должен совпадать с вашим доменом или IP.

---

## 2. Получение и установка сертификата

- После заказа сертификата у вас будут файлы:
  - `/etc/ssl/certs/your_domain.crt` (сертификат)
  - `/etc/ssl/certs/your_domain.ca-bundle` (цепочка доверия)
  - `/etc/ssl/private/your_domain.key` (приватный ключ, уже есть)

---

## 3. Настройка nginx для HTTPS

Установите nginx:
```bash
sudo apt update
sudo apt install nginx
```

Создайте или отредактируйте конфиг:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;  # или ваш IP

    ssl_certificate /etc/ssl/certs/your_domain.crt;
    ssl_certificate_key /etc/ssl/private/your_domain.key;
    ssl_trusted_certificate /etc/ssl/certs/your_domain.ca-bundle;

    location / {
        proxy_pass http://127.0.0.1:8000;  # если FastAPI на 8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Перезапустите nginx:
```bash
sudo systemctl restart nginx
```

---

## 4. Открытие порта 443

```bash
sudo ufw allow 443/tcp
sudo ufw reload
```

---

## 5. Проверка работы

- Откройте в браузере: `https://your-domain.com/api/avatar/status_update`
- Должен быть ответ от сервера (405 или 404 для GET — это нормально).
- Проверьте сертификат через [SSL Labs](https://www.ssllabs.com/ssltest/).

---

## 6. Обновление webhook

- В сервисах (например, fal.ai) укажите новый адрес:
  `https://your-domain.com/api/avatar/status_update`

---

## 7. Советы и безопасность
- Никогда не публикуйте приватный ключ.
- Используйте только валидные сертификаты (Let's Encrypt — бесплатно).
- Для продакшена используйте доменное имя, а не IP.
- Следите за сроком действия сертификата.

---

**Если возникнут вопросы — смотрите логи nginx и FastAPI, проверяйте firewall и доступность порта 443.** 