#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера для обработки webhook от FAL AI
"""
import uvicorn
from app.api_server import app

if __name__ == "__main__":
    print("🚀 Запуск API сервера для webhook...")
    print("📡 Endpoint: http://localhost:8000/webhook/fal/status")
    print("🔍 Health check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменениях
        log_level="info"
    ) 