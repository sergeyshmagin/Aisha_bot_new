"""
Главное FastAPI приложение для обработки webhook от FAL AI
SSL-готово для продакшн использования
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from .core.config import settings, SSL_CERT_FULL_PATH, SSL_KEY_FULL_PATH
from .core.logger import setup_logging, get_api_logger
from .routers import fal_webhook

# Настройка логирования при старте
setup_logging()
logger = get_api_logger()

# Создание FastAPI приложения
app = FastAPI(
    title="Aisha Bot FAL Webhook API",
    description="API сервер для обработки webhook от FAL AI с SSL поддержкой",
    version="1.0.0",
    docs_url="/docs" if settings.API_DEBUG else None,
    redoc_url="/redoc" if settings.API_DEBUG else None,
    openapi_url="/openapi.json" if settings.API_DEBUG else None
)

# Middleware для безопасности
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["aibots.kz", "*.aibots.kz", "localhost", "127.0.0.1"]
)

# CORS middleware (ограниченный для продакшн)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aibots.kz"] if not settings.API_DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(fal_webhook.router)

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("🚀 Запуск FAL Webhook API сервера")
    logger.info(f"📡 SSL включен: {settings.SSL_ENABLED}")
    logger.info(f"🔒 Порт: {settings.API_PORT}")
    
    # Проверяем SSL сертификаты если включен SSL
    if settings.SSL_ENABLED:
        if SSL_CERT_FULL_PATH.exists() and SSL_KEY_FULL_PATH.exists():
            logger.info("✅ SSL сертификаты найдены")
        else:
            logger.warning("⚠️ SSL сертификаты не найдены!")
            logger.warning(f"Ожидается: {SSL_CERT_FULL_PATH}")
            logger.warning(f"Ожидается: {SSL_KEY_FULL_PATH}")

@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("🛑 Остановка FAL Webhook API сервера")

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Aisha Bot FAL Webhook API",
        "version": "1.0.0",
        "ssl_enabled": settings.SSL_ENABLED,
        "status": "running"
    }

def run_server():
    """Запуск сервера с SSL поддержкой"""
    ssl_config = {}
    
    if settings.SSL_ENABLED:
        if SSL_CERT_FULL_PATH.exists() and SSL_KEY_FULL_PATH.exists():
            ssl_config = {
                "ssl_certfile": str(SSL_CERT_FULL_PATH),
                "ssl_keyfile": str(SSL_KEY_FULL_PATH),
            }
            logger.info("🔒 SSL сертификаты загружены")
        else:
            logger.error("❌ SSL сертификаты не найдены, запуск без SSL")
            settings.SSL_ENABLED = False
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        **ssl_config
    )

if __name__ == "__main__":
    run_server() 