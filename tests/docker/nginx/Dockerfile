FROM nginx:alpine

# Копируем конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем директории для логов
RUN mkdir -p /var/log/nginx

# Устанавливаем curl для healthcheck
RUN apk add --no-cache curl

# Метаданные
LABEL maintainer="Aisha Bot Team"
LABEL version="2.0"
LABEL description="Nginx reverse proxy for Aisha Bot v2"

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"] 