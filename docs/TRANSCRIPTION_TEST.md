# 🎤 Тестирование транскрибации после исправлений

## ✅ Исправления развернуты успешно!

### 🔧 Что было исправлено:
- **ffmpeg установлен** в Docker образ
- **Путь storage исправлен** с `/opt/aisha-backend` на `/app/storage/temp`
- **Polling конфликты устранены** - только основной бот делает polling
- **Standby бот в режиме ожидания** - не конфликтует

## 🧪 Как протестировать транскрибацию:

### 1. 🎤 Отправьте голосовое сообщение
- Откройте Telegram
- Найдите бота `@KAZAI_Aisha_bot`
- Запишите и отправьте короткое голосовое сообщение (до 30 сек)

### 2. 📝 Мониторинг в реальном времени
```bash
# Следите за обработкой аудио
ssh aisha@192.168.0.10 'docker logs aisha-bot-polling-1 --follow | grep -E "(audio|transcript|ffmpeg)"'
```

### 3. 🔍 Быстрая диагностика
```bash
# Локально
./scripts/utils/debug-transcription.sh

# На сервере
ssh aisha@192.168.0.10 '/tmp/quick-debug.sh'
```

## 📊 Ожидаемые результаты:

### ✅ Успешная транскрибация:
```
[AUDIO_UNIVERSAL] Начинаем обработку аудио
[AudioService] Начало process_audio (ffmpeg pipeline)
[AudioService] Размер входных данных: XXXX байт
[AudioService] Определен формат: M4A/MP4
[AudioService] Конвертация в mp3 через ffmpeg
[AudioService] mp3-файл создан
[AudioService] Нарезка на чанки через ffmpeg
[AudioService] Получено чанков: X
[AudioService] Транскрибация чанка 1/X
[AudioService] Итоговая транскрибация: success=true
```

### ❌ Если есть проблемы:
- **Permission denied** - должно быть исправлено
- **ffprobe недоступен** - должно быть исправлено  
- **Конфликты polling** - должны быть устранены

## 🚨 Диагностика проблем:

### Проверка компонентов:
```bash
# ffmpeg
ssh aisha@192.168.0.10 'docker exec aisha-bot-polling-1 which ffmpeg'

# Директории
ssh aisha@192.168.0.10 'docker exec aisha-bot-polling-1 ls -la /app/storage/'

# Конфликты
ssh aisha@192.168.0.10 'docker logs aisha-bot-polling-1 --since 5m | grep -i conflict'
```

### Статус ботов:
```bash
ssh aisha@192.168.0.10 'docker ps --filter "name=aisha-bot"'
```

## 📈 Мониторинг производительности:

### Статистика обработки:
```bash
ssh aisha@192.168.0.10 '
handled=$(docker logs aisha-bot-polling-1 --since 10m | grep -c "is handled" || echo 0)
errors=$(docker logs aisha-bot-polling-1 --since 10m | grep -c "ERROR" || echo 0)
audio=$(docker logs aisha-bot-polling-1 --since 10m | grep -c "audio.*processing" || echo 0)

echo "За последние 10 минут:"
echo "  • Обработано сообщений: $handled"
echo "  • Ошибок: $errors"  
echo "  • Обработка аудио: $audio"
'
```

## 🎯 Следующие шаги:

1. **Протестируйте транскрибацию** голосовыми сообщениями
2. **Проверьте качество** транскрипции на разных языках
3. **Мониторьте производительность** в течение дня
4. **Настройте staging окружение** для будущих изменений

## 🔧 Инструменты диагностики:

- `./scripts/utils/debug-transcription.sh` - полная диагностика
- `./scripts/production/fix-standby-bot.sh` - управление standby ботом  
- `./scripts/monitoring/monitor-production.sh` - общий мониторинг
- `ssh aisha@192.168.0.10 '/tmp/quick-debug.sh'` - быстрая проверка на сервере

---

**🎉 Результат:** Все критические проблемы исправлены, система готова к тестированию! 