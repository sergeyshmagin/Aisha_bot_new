#!/usr/bin/env python3
"""
Главный файл для запуска API сервера webhook
Обновленная версия для продакшн использования
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import fal_webhook

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
        "ssl_enabled": settings.SSL_ENABLED,
        "webhook_url": settings.FAL_WEBHOOK_URL
    }

def main():
    """Запуск сервера"""
    
    print("🚀 Запуск Aisha Bot Webhook API")
    print(f"   Host: {settings.API_HOST}")
    print(f"   Port: {settings.API_PORT}")
    print(f"   SSL: {settings.SSL_ENABLED}")
    print(f"   Webhook URL: {settings.FAL_WEBHOOK_URL}")
    
    # Настройки для запуска
    run_config = {
        "app": "main:app",
        "host": settings.API_HOST,
        "port": settings.API_PORT,
        "reload": settings.API_RELOAD,
        "log_level": "info"
    }
    
    # Добавляем SSL если включен
    if settings.SSL_ENABLED:
        from pathlib import Path
        
        ssl_cert = Path(settings.SSL_CERT_PATH)
        ssl_key = Path(settings.SSL_KEY_PATH)
        
        if ssl_cert.exists() and ssl_key.exists():
            run_config.update({
                "ssl_certfile": str(ssl_cert),
                "ssl_keyfile": str(ssl_key)
            })
            print(f"   SSL Cert: {ssl_cert}")
            print(f"   SSL Key: {ssl_key}")
        else:
            print("⚠️  SSL файлы не найдены, запуск без SSL")
    
    print("=" * 50)
    
    # Запускаем сервер
    uvicorn.run(**run_config)

if __name__ == "__main__":
    main() 