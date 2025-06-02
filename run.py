#!/usr/bin/env python3
"""
🤖 Запуск Aisha Bot v2 для локальной разработки

Этот скрипт запускает бота в режиме polling для локальной разработки
с подключением к удаленным сервисам (PostgreSQL, Redis, MinIO, API webhook)
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Устанавливаем рабочую директорию
os.chdir(PROJECT_ROOT)

if __name__ == "__main__":
    print("🏠 Запуск Aisha Bot v2 (локальная разработка)")
    print("📡 API сервер: aibots.kz:8443")
    print("🗄️  PostgreSQL: 192.168.0.4:5432")
    print("🔴 Redis: 192.168.0.3:6379")
    print("📦 MinIO: 192.168.0.4:9000")
    print("🔄 Режим: polling (локальная разработка)")
    print()
    
    try:
        # Импортируем и запускаем основное приложение
        from app.main import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
