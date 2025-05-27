# 🐍 Исправление проблемы с импортами Python

## ❗ Проблема
```bash
ModuleNotFoundError: No module named 'app.services.storage'
```

## 🎯 Анализ проблемы

**Причина**: Python не может найти модуль `app.services.storage` при запуске через `python -m app.main`

**Корневая причина**: 
- PYTHONPATH не включает корневую директорию проекта `/opt/aisha-backend`
- Рабочая директория может быть неправильной
- Структура импортов требует корректного разрешения путей

## 🚀 Быстрое решение

### 1. Автоматическое исправление
```bash
cd /opt/aisha-backend
chmod +x fix_import_issue.sh
./fix_import_issue.sh
```

### 2. Ручное исправление

**Проверьте что вы в правильной директории:**
```bash
cd /opt/aisha-backend
pwd  # Должно быть: /opt/aisha-backend
```

**Активируйте виртуальное окружение:**
```bash
source .venv/bin/activate
```

**Запустите с правильным PYTHONPATH:**
```bash
# Вариант 1: через переменную окружения
PYTHONPATH=/opt/aisha-backend python -m app.main

# Вариант 2: через обертку (создается автоматически)
python run_bot.py

# Вариант 3: через systemd (рекомендуется для продакшена)
systemctl start aisha-bot.service
```

## 📁 Проверка структуры

Убедитесь что структура корректна:
```bash
cd /opt/aisha-backend
tree app/services/storage -a
```

Должно быть:
```
app/services/storage/
├── __init__.py          # Экспортирует StorageService
├── minio.py             # Класс MinioStorage
└── __pycache__/
```

## 🔧 Обертки для запуска

Скрипт создает удобные обертки:

### `run_bot.py` - для основного бота
```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Исправляет PYTHONPATH автоматически
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import main
main()
```

### `run_api.py` - для API сервера
```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Исправляет PYTHONPATH автоматически
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from api_server.app.main import app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
```

## ✅ Проверка решения

```bash
cd /opt/aisha-backend

# Тест импорта
python -c "from app.services.storage import StorageService; print('✅ Импорт работает')"

# Тест основного приложения
python run_bot.py --help

# Тест API сервера  
python run_api.py &
curl http://localhost:8000/health
```

## 🎯 Для продакшена

Используйте systemd сервисы (уже настроены):

```bash
# Основной бот
systemctl start aisha-bot.service
systemctl status aisha-bot.service

# API сервер
systemctl start aisha-api.service  
systemctl status aisha-api.service
```

## 🚨 Если проблема персистирует

1. **Проверьте права доступа:**
   ```bash
   ls -la /opt/aisha-backend/app/services/storage/
   ```

2. **Проверьте виртуальное окружение:**
   ```bash
   which python
   echo $VIRTUAL_ENV
   ```

3. **Проверьте Python path:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

4. **Переустановите зависимости:**
   ```bash
   cd /opt/aisha-backend
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 🎉 Итоговый результат

✅ **Импорты работают** - `app.services.storage` находится корректно  
✅ **Обертки созданы** - `run_bot.py` и `run_api.py`  
✅ **PYTHONPATH исправлен** - все модули доступны  
✅ **Готово к запуску** - используйте обертки или systemd  

**Рекомендация**: Используйте `python run_bot.py` вместо `python -m app.main` для избежания проблем с путями. 