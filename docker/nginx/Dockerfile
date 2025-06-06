FROM nginx:1.25-alpine

# Устанавливаем часовой пояс
ENV TZ=Asia/Almaty
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Almaty /etc/localtime && \
    echo "Asia/Almaty" > /etc/timezone

# Устанавливаем необходимые утилиты
RUN apk add --no-cache \
    curl \
    openssl \
    ca-certificates

# Создаем пользователя nginx с правильными правами
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Создаем необходимые директории
RUN mkdir -p /var/log/nginx /var/cache/nginx/proxy_temp \
    && chown -R nginx:nginx /var/log/nginx /var/cache/nginx

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем конфигурацию для logrotate
RUN echo '#!/bin/sh' > /etc/periodic/daily/nginx-logrotate && \
    echo 'kill -USR1 $(cat /var/run/nginx.pid 2>/dev/null) 2>/dev/null || true' >> /etc/periodic/daily/nginx-logrotate && \
    chmod +x /etc/periodic/daily/nginx-logrotate

# Проверяем конфигурацию nginx
RUN nginx -t

# Метаданные
LABEL maintainer="Aisha Bot Team"
LABEL version="2.1"
LABEL description="Production Nginx reverse proxy for Aisha Bot v2"

# Переключаемся на непривилегированного пользователя
USER nginx

EXPOSE 8443

# Создаем healthcheck скрипт
COPY --chown=nginx:nginx healthcheck.sh /usr/local/bin/healthcheck.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -k -f https://localhost:8443/health || exit 1

CMD ["nginx", "-g", "daemon off;"] 