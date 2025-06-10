#!/bin/bash

# 🧹 Безопасная очистка продакшн среды
# Удаляет ненужные ресурсы, сохраняя критически важные

set -euo pipefail

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >&2
}

# Критические сети, которые НЕ нужно удалять
CRITICAL_NETWORKS=("aisha_cluster" "aisha_bot_cluster" "bridge" "host" "none")

safe_cleanup_containers() {
    log "🧹 Очистка остановленных контейнеров..."
    
    # Удаляем только остановленные контейнеры
    stopped_containers=$(docker ps -aq --filter "status=exited")
    if [[ -n "$stopped_containers" ]]; then
        docker rm $stopped_containers
        log "✅ Удалены остановленные контейнеры"
    else
        log "ℹ️  Остановленных контейнеров не найдено"
    fi
}

safe_cleanup_images() {
    log "🧹 Очистка неиспользуемых образов..."
    
    # Удаляем dangling образы
    dangling_images=$(docker images -f "dangling=true" -q)
    if [[ -n "$dangling_images" ]]; then
        docker rmi $dangling_images
        log "✅ Удалены dangling образы"
    else
        log "ℹ️  Dangling образов не найдено"
    fi
}

safe_cleanup_volumes() {
    log "🧹 Очистка неиспользуемых volumes..."
    
    # Удаляем только неиспользуемые volumes
    unused_volumes=$(docker volume ls -f "dangling=true" -q)
    if [[ -n "$unused_volumes" ]]; then
        docker volume rm $unused_volumes
        log "✅ Удалены неиспользуемые volumes"
    else
        log "ℹ️  Неиспользуемых volumes не найдено"
    fi
}

safe_cleanup_networks() {
    log "🧹 Очистка неиспользуемых сетей..."
    
    # Получаем список всех сетей
    all_networks=$(docker network ls --format "{{.Name}}")
    
    for network in $all_networks; do
        # Проверяем, не является ли сеть критической
        is_critical=false
        for critical in "${CRITICAL_NETWORKS[@]}"; do
            if [[ "$network" == "$critical" ]]; then
                is_critical=true
                break
            fi
        done
        
        if [[ "$is_critical" == "false" ]]; then
            # Проверяем, используется ли сеть
            network_usage=$(docker network inspect "$network" --format "{{.Containers}}" 2>/dev/null || echo "{}")
            if [[ "$network_usage" == "{}" ]]; then
                log_warning "🗑️  Удаление неиспользуемой сети: $network"
                docker network rm "$network" 2>/dev/null || log_warning "Не удалось удалить сеть $network"
            else
                log "ℹ️  Сеть $network используется, пропускаем"
            fi
        else
            log "🔒 Критическая сеть $network защищена от удаления"
        fi
    done
}

cleanup_temp_files() {
    log "🧹 Очистка временных файлов..."
    
    # Очищаем /tmp от архивов
    rm -f /tmp/*.tar.gz /tmp/*.zip /tmp/*.tar 2>/dev/null || true
    
    # Очищаем логи старше 7 дней
    if [[ -d "logs" ]]; then
        find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    fi
    
    log "✅ Временные файлы очищены"
}

show_cleanup_summary() {
    log "📊 Итоги очистки:"
    
    echo "=== Активные контейнеры ==="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    
    echo -e "\n=== Защищенные сети ==="
    for network in "${CRITICAL_NETWORKS[@]}"; do
        if docker network ls | grep -q "$network"; then
            echo "✅ $network"
        else
            echo "❌ $network (отсутствует!)"
        fi
    done
    
    echo -e "\n=== Использование диска ==="
    docker system df
}

ensure_critical_networks() {
    log "🔧 Проверка критических сетей..."
    
    for network in "${CRITICAL_NETWORKS[@]:0:2}"; do  # Проверяем только aisha сети
        if ! docker network ls | grep -q "$network"; then
            log_warning "⚠️  Критическая сеть $network отсутствует, создаем..."
            if [[ "$network" == "aisha_bot_cluster" ]]; then
                docker network create --subnet=172.26.0.0/16 "$network"
            else
                docker network create "$network"
            fi
            log "✅ Критическая сеть $network создана"
        fi
    done
}

main() {
    log "🚀 Запуск безопасной очистки"
    
    # Проверяем права
    if [[ $EUID -eq 0 ]]; then
        log_warning "⚠️  Скрипт запущен от root, будьте осторожны"
    fi
    
    # Убеждаемся, что критические сети существуют
    ensure_critical_networks
    
    # Выполняем очистку
    safe_cleanup_containers
    safe_cleanup_images
    safe_cleanup_volumes
    safe_cleanup_networks
    cleanup_temp_files
    
    # Показываем итоги
    show_cleanup_summary
    
    log "✅ Безопасная очистка завершена"
    log "🔒 Критические ресурсы защищены"
}

# Запуск скрипта
main "$@" 