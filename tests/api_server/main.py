#!/usr/bin/env python3
"""
Главный файл для запуска API сервера webhook
Обновленная версия для продакшн использования
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Исправленные импорты для работы в структуре api_server
try:
    # Пробуем импортировать из api_server.app (когда запускается через launch_webhook_api.py)
    from api_server.app.core.config import settings
    from api_server.app.routers import fal_webhook
except ImportError:
    try:
        # Пробуем импортировать из app (когда запускается напрямую из api_server/)
        from app.core.config import settings
        from app.routers import fal_webhook
    except ImportError:
        # Последняя попытка - относительные импорты
        from .app.core.config import settings
        from .app.routers import fal_webhook

# Создаем FastAPI приложение
app = FastAPI(
    title="Aisha Bot Webhook API",
    description="API сервер для обработки webhook от FAL AI",
    version="2.0.0"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(fal_webhook.router)

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Aisha Bot Webhook API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "webhook": "/api/v1/avatar/status_update",
            "test": "/api/v1/avatar/test_webhook"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "ssl_enabled": getattr(settings, 'SSL_ENABLED', False),
        "webhook_url": getattr(settings, 'FAL_WEBHOOK_URL', 'not_configured')
    }

def main():
    """Запуск сервера"""
    
    print("🚀 Запуск Aisha Bot Webhook API")
    
    # Безопасное получение настроек с значениями по умолчанию
    api_host = getattr(settings, 'API_HOST', '0.0.0.0')
    api_port = getattr(settings, 'API_PORT', 8443)
    ssl_enabled = getattr(settings, 'SSL_ENABLED', False)
    api_reload = getattr(settings, 'API_RELOAD', False)
    webhook_url = getattr(settings, 'FAL_WEBHOOK_URL', 'not_configured')
    
    print(f"   Host: {api_host}")
    print(f"   Port: {api_port}")
    print(f"   SSL: {ssl_enabled}")
    print(f"   Webhook URL: {webhook_url}")
    
    # Настройки для запуска
    run_config = {
        "app": "main:app",
        "host": api_host,
        "port": api_port,
        "reload": api_reload,
        "log_level": "info"
    }
    
    # Добавляем SSL если включен
    if ssl_enabled:
        from pathlib import Path
        
        ssl_cert_path = getattr(settings, 'SSL_CERT_PATH', '')
        ssl_key_path = getattr(settings, 'SSL_KEY_PATH', '')
        
        if ssl_cert_path and ssl_key_path:
            ssl_cert = Path(ssl_cert_path)
            ssl_key = Path(ssl_key_path)
            
            if ssl_cert.exists() and ssl_key.exists():
                run_config.update({
                    "ssl_certfile": str(ssl_cert),
                    "ssl_keyfile": str(ssl_key)
                })
                print(f"   SSL Cert: {ssl_cert}")
                print(f"   SSL Key: {ssl_key}")
            else:
                print("⚠️  SSL файлы не найдены, запуск без SSL")
        else:
            print("⚠️  SSL пути не настроены, запуск без SSL")
    
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(**run_config)

if __name__ == "__main__":
    main() 