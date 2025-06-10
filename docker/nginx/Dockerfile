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

# Используем существующего пользователя nginx и создаем необходимые директории
RUN mkdir -p /var/log/nginx /var/cache/nginx/proxy_temp \
    && chown -R nginx:nginx /var/log/nginx /var/cache/nginx

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем конфигурацию для logrotate
RUN echo '#!/bin/sh' > /etc/periodic/daily/nginx-logrotate && \
    echo 'kill -USR1 $(cat /var/run/nginx.pid 2>/dev/null) 2>/dev/null || true' >> /etc/periodic/daily/nginx-logrotate && \
    chmod +x /etc/periodic/daily/nginx-logrotate

# Метаданные
LABEL maintainer="Aisha Bot Team"
LABEL version="2.1"
LABEL description="Production Nginx reverse proxy for Aisha Bot v2"

# Создаем healthcheck скрипт
COPY --chown=root:root healthcheck.sh /usr/local/bin/healthcheck.sh
RUN chmod +x /usr/local/bin/healthcheck.sh

EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Создаем startup script для проверки конфигурации
RUN echo '#!/bin/sh' > /docker-entrypoint.d/90-check-config.sh && \
    echo 'nginx -t' >> /docker-entrypoint.d/90-check-config.sh && \
    chmod +x /docker-entrypoint.d/90-check-config.sh

CMD ["nginx", "-g", "daemon off;"] 