#!/usr/bin/env python3
"""
🏠 Скрипт настройки локальной разработки

Настраивает локальное окружение для работы с удаленным API сервером aibots.kz
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


def info(message: str) -> None:
    """Информационное сообщение"""
    print(f"📋 {message}")


def success(message: str) -> None:
    """Сообщение об успехе"""
    print(f"✅ {message}")


def warning(message: str) -> None:
    """Предупреждение"""
    print(f"⚠️  {message}")


def error(message: str) -> None:
    """Ошибка"""
    print(f"❌ {message}")


def run_command(command: str, check: bool = True) -> Optional[subprocess.CompletedProcess]:
    """Выполнить команду в shell"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        error(f"Ошибка выполнения команды: {command}")
        error(f"Вывод: {e.stdout}")
        error(f"Ошибки: {e.stderr}")
        return None


def check_api_server() -> bool:
    """Проверить доступность удаленного API сервера"""
    info("Проверяю доступность API сервера aibots.kz:8443...")
    
    result = run_command("curl -s https://aibots.kz:8443/health", check=False)
    if result and result.returncode == 0:
        success("API сервер доступен")
        return True
    else:
        error("API сервер недоступен")
        return False


def check_webhook_endpoint() -> bool:
    """Проверить webhook endpoint"""
    info("Проверяю webhook endpoint...")
    
    result = run_command("curl -s https://aibots.kz:8443/api/v1/webhook/status", check=False)
    if result and result.returncode == 0:
        success("Webhook endpoint работает")
        return True
    else:
        error("Webhook endpoint недоступен")
        return False


def check_env_file() -> bool:
    """Проверить конфигурацию .env"""
    env_file = Path(".env")
    
    if not env_file.exists():
        error("Файл .env не найден")
        return False
    
    info("Проверяю конфигурацию .env...")
    
    # Читаем конфигурацию
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем ключевые параметры
    required_vars = [
        "TELEGRAM_TOKEN",
        "DATABASE_URL", 
        "FAL_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        error(f"Не настроены переменные: {', '.join(missing_vars)}")
        return False
    
    success("Конфигурация .env корректна")
    return True


def check_virtual_env() -> bool:
    """Проверить виртуальное окружение"""
    if sys.prefix == sys.base_prefix:
        error("Виртуальное окружение не активировано")
        info("Выполните: source .venv/bin/activate (Linux/Mac) или .venv\\Scripts\\activate (Windows)")
        return False
    
    success("Виртуальное окружение активировано")
    return True


def check_dependencies() -> bool:
    """Проверить зависимости"""
    info("Проверяю установленные зависимости...")
    
    required_packages = [
        "aiogram",
        "sqlalchemy", 
        "asyncpg",
        "fastapi",
        "pytest"
    ]
    
    missing_packages = []
    for package in required_packages:
        result = run_command(f"python -c 'import {package}'", check=False)
        if result and result.returncode != 0:
            missing_packages.append(package)
    
    if missing_packages:
        error(f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        info("Выполните: pip install -r requirements.txt")
        return False
    
    success("Все зависимости установлены")
    return True


def check_database_connection() -> bool:
    """Проверить подключение к базе данных"""
    info("Проверяю подключение к базе данных...")
    
    test_script = """
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

async def test_db():
    try:
        engine = create_async_engine(os.getenv('DATABASE_URL'))
        async with engine.begin() as conn:
            result = await conn.execute('SELECT 1')
            await conn.close()
        await engine.dispose()
        print('OK')
    except Exception as e:
        print(f'ERROR: {e}')

asyncio.run(test_db())
"""
    
    result = run_command(f"python -c \"{test_script}\"", check=False)
    if result and "OK" in result.stdout:
        success("Подключение к базе данных работает")
        return True
    else:
        error("Ошибка подключения к базе данных")
        if result:
            error(f"Детали: {result.stdout}")
        return False


def check_redis_connection() -> bool:
    """Проверить подключение к Redis"""
    info("Проверяю подключение к Redis...")
    
    test_script = """
import os
import redis

try:
    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', 6379))
    password = os.getenv('REDIS_PASSWORD')
    
    r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
    r.ping()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
"""
    
    result = run_command(f"python -c \"{test_script}\"", check=False)
    if result and "OK" in result.stdout:
        success("Подключение к Redis работает")
        return True
    else:
        error("Ошибка подключения к Redis")
        if result:
            error(f"Детали: {result.stdout}")
        return False


def display_summary() -> None:
    """Показать сводку для разработки"""
    info("\n🎯 Настройка локальной разработки завершена!")
    print("\n📋 Архитектура:")
    print("  🤖 Telegram Bot (localhost) - polling mode")
    print("  📡 API Server (aibots.kz:8443) - webhook endpoint")
    print("  🗄️  PostgreSQL (192.168.0.4:5432) - production DB")
    print("  🔴 Redis (192.168.0.3:6379) - production cache")
    print("  📦 MinIO (192.168.0.4:9000) - production storage")
    
    print("\n🚀 Команды для разработки:")
    print("  python -m app.main              # Запуск бота")
    print("  pytest tests/ -v                # Запуск тестов")
    print("  pytest --cov=app --cov-report=html  # Тесты с покрытием")
    
    print("\n🔧 Полезные ссылки:")
    print("  https://aibots.kz:8443/health               # Health check API")
    print("  https://aibots.kz:8443/api/v1/webhook/status # Webhook status")
    
    print("\n📖 Документация:")
    print("  docs/LOCAL_DEVELOPMENT_SETUP.md    # Подробный гайд")
    print("  docs/PLANNING.md                   # Текущие задачи")
    print("  docs/CURRENT_TASKS.md              # Приоритеты")


def main():
    """Основная функция"""
    print("🏠 Настройка локальной разработки Aisha Bot v2")
    print("=" * 50)
    
    checks = [
        ("Виртуальное окружение", check_virtual_env),
        ("Конфигурация .env", check_env_file),
        ("Зависимости Python", check_dependencies),
        ("API сервер aibots.kz", check_api_server),
        ("Webhook endpoint", check_webhook_endpoint),
        ("База данных PostgreSQL", check_database_connection),
        ("Redis кэш", check_redis_connection),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔍 {name}:")
        if check_func():
            passed += 1
        else:
            warning(f"Проблема с: {name}")
    
    print(f"\n📊 Результат: {passed}/{total} проверок пройдено")
    
    if passed == total:
        success("Все проверки пройдены! Локальное окружение готово к разработке")
        display_summary()
    else:
        error("Некоторые проверки не пройдены. Исправьте проблемы перед началом разработки")
        print("\n💡 Подсказки:")
        print("  1. Активируйте виртуальное окружение: source .venv/bin/activate")
        print("  2. Установите зависимости: pip install -r requirements.txt")
        print("  3. Проверьте настройки в .env файле")
        print("  4. Убедитесь что удаленные сервисы доступны")
    
    return passed == total


if __name__ == "__main__":
    success_status = main()
    sys.exit(0 if success_status else 1) 