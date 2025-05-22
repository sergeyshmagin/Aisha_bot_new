# Администрирование и запуск

> **База данных:** Основная рабочая БД — `aisha`. Все параметры подключения задаются через `.env` и `alembic.ini`.

## Размещение на сервере
- Проект находится в директории `/opt/aisha_bot`

## Запуск и остановка сервисов (systemd)
- Запуск фронтенда: `sudo systemctl start aisha-bot`
- Остановка фронтенда: `sudo systemctl stop aisha-bot`
- Статус фронтенда: `sudo systemctl status aisha-bot`
- Перезапуск фронтенда: `sudo systemctl restart aisha-bot`

- Запуск бэкенда: `sudo systemctl start aisha-backend`
- Остановка бэкенда: `sudo systemctl stop aisha-backend`
- Статус бэкенда: `sudo systemctl status aisha-backend`
- Перезапуск бэкенда: `sudo systemctl restart aisha-backend`

## Просмотр логов
- `journalctl -u aisha-bot -f`
- `journalctl -u aisha-backend -f`

## Обновление кода
- Перейти в директорию `/opt/aisha_bot`
- Выполнить `git pull`
- Перезапустить сервисы через systemctl

---

TODO: Добавить примеры типовых операций и рекомендации по безопасности.
