#!/usr/bin/env python3
"""
Исправленный запуск webhook API для деплоя через WinSCP
Устраняет проблемы с путями и зависимостями
"""
import uvicorn
import os
import sys
from pathlib import Path

def setup_environment():
    """Настройка окружения для работы API"""
    # Определяем корневую папку проекта
    project_root = Path(__file__).parent.absolute()
    
    # Добавляем пути для импорта
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "api_server"))
    
    # Устанавливаем рабочую директорию
    os.chdir(project_root)
    
    print(f"🔧 Project root: {project_root}")
    print(f"🔧 Working directory: {os.getcwd()}")
    
    return project_root

def main():
    """Главная функция запуска"""
    print("🚀 Запуск Aisha Bot Webhook API")
    
    # Настраиваем окружение
    project_root = setup_environment()
    
    # Проверяем наличие api_server/main.py
    api_main = project_root / "api_server" / "main.py"
    if not api_main.exists():
        print(f"❌ Файл {api_main} не найден!")
        print("📁 Проверьте структуру проекта")
        return
    
    # Импортируем и запускаем API
    try:
        from api_server.main import app
        
        print("✅ API приложение импортировано успешно")
        print("📡 API сервер: http://0.0.0.0:8000")
        print("📡 Webhook endpoint (через Nginx): https://aibots.kz:8443/api/v1/avatar/status_update")
        print("🔍 Health check: http://0.0.0.0:8000/health")
        
        # Запускаем сервер
        uvicorn.run(
            app,
            host="0.0.0.0",  # Слушаем все интерфейсы
            port=8000,       # API сервер на 8000, Nginx на 8443
            log_level="info",
            reload=False
        )
        
    except ImportError as e:
        print(f"❌ Ошибка импорта API: {e}")
        print("📦 Проверьте установку зависимостей: pip install -r requirements_api.txt")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main() 