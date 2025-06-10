#!/bin/bash

# 🔐 Настройка HTTPS для Docker Registry на 192.168.0.4
# Этот скрипт настраивает SSL сертификаты и конфигурацию для безопасного реестра

set -euo pipefail

# Переменные
REGISTRY_HOST="192.168.0.4"
REGISTRY_PORT="5000"
REGISTRY_DIR="/opt/docker-registry"
CERTS_DIR="$REGISTRY_DIR/certs"
CONFIG_DIR="$REGISTRY_DIR/config"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

create_self_signed_cert() {
    log "🔐 Создание самоподписанного SSL сертификата..."
    
    mkdir -p "$CERTS_DIR"
    
    # Создаем конфигурацию для сертификата
    cat > "$CERTS_DIR/registry.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C=KZ
ST=Almaty
L=Almaty
O=Aisha Bot
OU=IT Department
CN=$REGISTRY_HOST

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $REGISTRY_HOST
DNS.2 = localhost
IP.1 = $REGISTRY_HOST
IP.2 = 127.0.0.1
EOF

    # Генерируем приватный ключ
    openssl genrsa -out "$CERTS_DIR/registry.key" 4096
    
    # Создаем запрос на сертификат
    openssl req -new -key "$CERTS_DIR/registry.key" \
        -out "$CERTS_DIR/registry.csr" \
        -config "$CERTS_DIR/registry.conf"
    
    # Генерируем самоподписанный сертификат
    openssl x509 -req -days 365 \
        -in "$CERTS_DIR/registry.csr" \
        -signkey "$CERTS_DIR/registry.key" \
        -out "$CERTS_DIR/registry.crt" \
        -extensions v3_req \
        -extfile "$CERTS_DIR/registry.conf"
    
    # Устанавливаем правильные права
    chmod 600 "$CERTS_DIR/registry.key"
    chmod 644 "$CERTS_DIR/registry.crt"
    
    log "✅ SSL сертификат создан: $CERTS_DIR/registry.crt"
}

create_registry_config() {
    log "⚙️ Создание конфигурации Registry..."
    
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_DIR/config.yml" << EOF
version: 0.1
log:
  fields:
    service: registry
  level: info
storage:
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
http:
  addr: :5000
  tls:
    certificate: /certs/registry.crt
    key: /certs/registry.key
  debug:
    addr: :5001
    prometheus:
      enabled: true
      path: /metrics
  headers:
    X-Content-Type-Options: [nosniff]
    Access-Control-Allow-Origin: ['*']
    Access-Control-Allow-Methods: ['HEAD', 'GET', 'OPTIONS', 'DELETE']
    Access-Control-Allow-Headers: ['Authorization', 'Accept', 'Cache-Control']
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
EOF
    
    log "✅ Конфигурация создана: $CONFIG_DIR/config.yml"
}

create_docker_compose() {
    log "🐳 Создание docker-compose для HTTPS Registry..."
    
    cat > "$REGISTRY_DIR/docker-compose.yml" << EOF
version: '3.8'

services:
  registry:
    image: registry:2.8.3
    container_name: docker-registry-https
    restart: unless-stopped
    ports:
      - "5000:5000"
      - "5001:5001"  # Debug/metrics port
    volumes:
      - ./data:/var/lib/registry
      - ./certs:/certs:ro
      - ./config:/etc/docker/registry:ro
    environment:
      - REGISTRY_CONFIG_PATH=/etc/docker/registry/config.yml
    healthcheck:
      test: ["CMD", "wget", "--no-check-certificate", "-qO-", "https://localhost:5000/v2/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - registry-network

  # Web UI для управления registry (опционально)
  registry-ui:
    image: joxit/docker-registry-ui:main
    container_name: registry-ui
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - SINGLE_REGISTRY=true
      - REGISTRY_TITLE=Aisha Bot Registry
      - DELETE_IMAGES=true
      - SHOW_CONTENT_DIGEST=true
      - NGINX_PROXY_PASS_URL=https://registry:5000
      - SHOW_CATALOG_NB_TAGS=true
      - CATALOG_MIN_BRANCHES=1
      - CATALOG_MAX_BRANCHES=1
      - TAGLIST_PAGE_SIZE=100
      - REGISTRY_SECURED=false
      - CATALOG_ELEMENTS_LIMIT=1000
    depends_on:
      - registry
    networks:
      - registry-network

networks:
  registry-network:
    driver: bridge
EOF
    
    log "✅ Docker Compose создан: $REGISTRY_DIR/docker-compose.yml"
}

setup_client_cert() {
    log "🔧 Настройка клиентского сертификата..."
    
    # Копируем сертификат в системное хранилище
    if [[ -f "/etc/docker/certs.d" ]]; then
        DOCKER_CERTS_DIR="/etc/docker/certs.d/$REGISTRY_HOST:$REGISTRY_PORT"
        sudo mkdir -p "$DOCKER_CERTS_DIR"
        sudo cp "$CERTS_DIR/registry.crt" "$DOCKER_CERTS_DIR/ca.crt"
        log "✅ Сертификат установлен в Docker: $DOCKER_CERTS_DIR/ca.crt"
    fi
    
    # Создаем инструкции для других хостов
    cat > "$REGISTRY_DIR/client-setup.sh" << EOF
#!/bin/bash
# Скрипт для настройки клиентов Docker Registry

REGISTRY_HOST="$REGISTRY_HOST"
REGISTRY_PORT="$REGISTRY_PORT"

# Создание директории для сертификатов
sudo mkdir -p "/etc/docker/certs.d/\${REGISTRY_HOST}:\${REGISTRY_PORT}"

# Копирование сертификата (загрузите registry.crt на клиентский хост)
sudo cp registry.crt "/etc/docker/certs.d/\${REGISTRY_HOST}:\${REGISTRY_PORT}/ca.crt"

# Перезапуск Docker службы
sudo systemctl restart docker

echo "✅ Клиент настроен для HTTPS Registry"
echo "Теперь можно использовать: docker push \${REGISTRY_HOST}:\${REGISTRY_PORT}/image:tag"
EOF
    
    chmod +x "$REGISTRY_DIR/client-setup.sh"
    log "✅ Скрипт для клиентов создан: $REGISTRY_DIR/client-setup.sh"
}

deploy_registry() {
    log "🚀 Развертывание HTTPS Docker Registry..."
    
    cd "$REGISTRY_DIR"
    
    # Останавливаем старый registry если есть
    docker-compose down 2>/dev/null || true
    
    # Запускаем новый HTTPS registry
    docker-compose up -d
    
    # Проверяем статус
    sleep 10
    if docker-compose ps | grep -q "Up"; then
        log "✅ HTTPS Docker Registry запущен успешно"
        log "🌐 Registry URL: https://$REGISTRY_HOST:$REGISTRY_PORT"
        log "🖥️  Web UI: http://$REGISTRY_HOST:8080"
    else
        log_error "❌ Ошибка запуска Registry"
        docker-compose logs
        exit 1
    fi
}

show_usage_examples() {
    log "📖 Примеры использования HTTPS Registry:"
    cat << EOF

1. Тегирование образа:
   docker tag my-image:latest $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

2. Push образа:
   docker push $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

3. Pull образа:
   docker pull $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

4. Список репозиториев:
   curl -k https://$REGISTRY_HOST:$REGISTRY_PORT/v2/_catalog

5. Просмотр тегов:
   curl -k https://$REGISTRY_HOST:$REGISTRY_PORT/v2/my-image/tags/list

📁 Файлы сертификатов:
   - Сертификат: $CERTS_DIR/registry.crt
   - Ключ: $CERTS_DIR/registry.key
   - Конфигурация: $CONFIG_DIR/config.yml

🔧 Для настройки клиентов на других хостах:
   - Скопируйте registry.crt на клиентский хост
   - Запустите: $REGISTRY_DIR/client-setup.sh

EOF
}

main() {
    log "🔐 Начинаем настройку HTTPS Docker Registry на $REGISTRY_HOST:$REGISTRY_PORT"
    
    # Проверяем права
    if [[ $EUID -eq 0 ]]; then
        log_error "Не запускайте скрипт от root"
        exit 1
    fi
    
    # Создаем базовую директорию
    sudo mkdir -p "$REGISTRY_DIR"
    sudo chown -R "$USER:$USER" "$REGISTRY_DIR"
    
    # Выполняем настройку
    create_self_signed_cert
    create_registry_config  
    create_docker_compose
    setup_client_cert
    deploy_registry
    show_usage_examples
    
    log "🎉 HTTPS Docker Registry настроен успешно!"
    log_error "⚠️  ВАЖНО: Сертификат самоподписанный. Для продакшн используйте сертификат от CA"
}

# Запуск скрипта
main "$@" 