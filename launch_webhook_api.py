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
        from api_server.app.core.config import settings
        
        print("✅ API приложение импортировано успешно")
        
        # Используем настройки из конфигурации
        api_host = getattr(settings, 'API_HOST', '0.0.0.0')
        api_port = getattr(settings, 'API_PORT', 8443)
        ssl_enabled = getattr(settings, 'SSL_ENABLED', False)
        webhook_url = getattr(settings, 'FAL_WEBHOOK_URL', 'not_configured')
        
        print(f"📡 API сервер: {'https' if ssl_enabled else 'http'}://{api_host}:{api_port}")
        print(f"📡 Webhook endpoint: {webhook_url}")
        print(f"🔍 Health check: {'https' if ssl_enabled else 'http'}://{api_host}:{api_port}/health")
        
        # Настройки для запуска
        run_config = {
            "app": app,
            "host": api_host,
            "port": api_port,
            "log_level": "info",
            "reload": False
        }
        
        # Добавляем SSL если включен
        if ssl_enabled:
            ssl_cert_path = getattr(settings, 'SSL_CERT_PATH', '')
            ssl_key_path = getattr(settings, 'SSL_KEY_PATH', '')
            
            if ssl_cert_path and ssl_key_path:
                ssl_cert = project_root / ssl_cert_path
                ssl_key = project_root / ssl_key_path
                
                if ssl_cert.exists() and ssl_key.exists():
                    run_config.update({
                        "ssl_certfile": str(ssl_cert),
                        "ssl_keyfile": str(ssl_key)
                    })
                    print(f"🔒 SSL Cert: {ssl_cert}")
                    print(f"🔒 SSL Key: {ssl_key}")
                else:
                    print("⚠️  SSL файлы не найдены, запуск без SSL")
            else:
                print("⚠️  SSL пути не настроены, запуск без SSL")
        
        # Запускаем сервер
        uvicorn.run(**run_config)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта API: {e}")
        print("📦 Проверьте установку зависимостей: pip install -r requirements_api.txt")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main()
