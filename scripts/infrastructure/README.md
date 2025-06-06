# 🏗️ Scripts - Infrastructure

Скрипты для управления инфраструктурой системы Aisha Bot.

## 📂 Содержание

- `nginx-management.sh` - Управление nginx сервером
- `production-setup.sh` - Настройка продакшн сервера
- `registry-setup.sh` - Настройка Docker Registry

## 🔧 Описание скриптов

### nginx-management.sh
Управление nginx сервером с SSL:
- Установка и настройка nginx
- Генерация SSL сертификатов
- Настройка reverse proxy
- Управление доменами

### production-setup.sh
Полная настройка продакшн сервера:
- Установка Docker и Docker Compose
- Настройка firewall
- Создание пользователей
- Базовая конфигурация безопасности

### registry-setup.sh
Настройка Docker Registry:
- Установка и конфигурация Registry
- Настройка insecure registry
- Создание SSL сертификатов
- Тестирование подключения

## 🚀 Использование

```bash
# Настройка продакшн сервера
./scripts/infrastructure/production-setup.sh

# Настройка nginx
./scripts/infrastructure/nginx-management.sh

# Настройка Docker Registry
./scripts/infrastructure/registry-setup.sh
``` 