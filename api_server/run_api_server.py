#!/usr/bin/env python3
"""
Скрипт запуска API сервера для обработки webhook от FAL AI
Поддерживает SSL для продакшн использования
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Устанавливаем переменные окружения для API сервера
os.environ.setdefault("API_SERVER_MODE", "true")

from app.main import run_server

if __name__ == "__main__":
    print("🚀 Запуск FAL Webhook API сервера")
    print("📡 Endpoint: https://aibots.kz:8443/api/v1/avatar/status_update")
    print("🔒 SSL включен для FAL AI webhook")
    print("🔍 Health check: https://aibots.kz:8443/health")
    print("📊 Webhook status: https://aibots.kz:8443/api/v1/webhook/status")
    print()
    
    run_server() 