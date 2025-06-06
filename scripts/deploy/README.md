# 🚀 Scripts - Deploy

Скрипты для развертывания системы Aisha Bot.

## 📂 Структура

```
scripts/
├── deploy/                 # Скрипты развертывания
│   ├── webhook-complete.sh  # Полное развертывание webhook API
│   ├── fix-registry.sh      # Исправление Docker Registry
│   ├── setup-autostart.sh   # Настройка автозапуска сервисов
│   └── setup-registry.sh    # Быстрая настройка Registry
├── infrastructure/         # Управление инфраструктурой
│   ├── nginx-management.sh  # Управление nginx
│   ├── production-setup.sh  # Настройка продакшн сервера
│   └── registry-setup.sh    # Настройка Docker Registry
├── maintenance/            # Скрипты обслуживания
│   ├── check_*.py          # Проверки состояния системы
│   ├── fix_*.py           # Исправления
│   └── manage_*.py        # Управление компонентами
├── testing/               # Тестирование
└── utils/                 # Утилиты
```

## 🎯 Основные скрипты развертывания

### `webhook-complete.sh`
Полное развертывание webhook API с проверками:
- Сборка Docker образов
- Отправка в registry
- Развертывание на продакшн
- Проверка работоспособности

### `fix-registry.sh`
Быстрое исправление проблем с Docker Registry

### `setup-autostart.sh`
Настройка автозапуска всех сервисов инфраструктуры

## 🔧 Использование

```bash
# Полное развертывание
./scripts/deploy/webhook-complete.sh

# Исправление registry
./scripts/deploy/fix-registry.sh

# Настройка автозапуска
./scripts/deploy/setup-autostart.sh
```

## 📋 Требования

- SSH доступ к серверам
- Docker установлен на всех серверах
- SSL сертификаты в `ssl_certificate/` 