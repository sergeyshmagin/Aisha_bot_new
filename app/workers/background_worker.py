#!/usr/bin/env python3
"""
Background Worker для Aisha Bot
Обрабатывает фоновые задачи без polling
"""

import asyncio
import logging
import signal
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class BackgroundWorker:
    """Фоновый воркер для обработки задач без polling"""
    
    def __init__(self):
        self.is_running = False
        self.tasks: list = []
        
    async def start(self):
        """Запуск фонового воркера"""
        logger.info(f"🔄 Запуск Background Worker - {settings.INSTANCE_ID}")
        
        self.is_running = True
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            # Запускаем основные задачи
            await self._run_worker_tasks()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в Background Worker: {e}")
            raise
        
    async def _run_worker_tasks(self):
        """Основной цикл выполнения задач"""
        logger.info("⚙️ Запуск основного цикла Background Worker")
        
        while self.is_running:
            try:
                # Здесь будут различные фоновые задачи:
                # - Очистка временных файлов
                # - Обработка отложенных задач
                # - Мониторинг состояния системы
                # - Периодические проверки
                
                await self._cleanup_temp_files()
                await self._process_background_tasks()
                
                # Пауза между циклами
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("🛑 Background Worker получил сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле Background Worker: {e}")
                await asyncio.sleep(10)
                
        logger.info("✅ Background Worker завершен")
        
    async def _cleanup_temp_files(self):
        """Очистка временных файлов старше определенного времени"""
        try:
            import os
            import time
            from pathlib import Path
            
            temp_dir = Path("/app/storage/temp")
            if not temp_dir.exists():
                return
                
            current_time = time.time()
            max_age = 3600  # 1 час
            
            for file_path in temp_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        try:
                            file_path.unlink()
                            logger.debug(f"🗑️ Удален временный файл: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Не удалось удалить файл {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки временных файлов: {e}")
            
    async def _process_background_tasks(self):
        """Обработка фоновых задач"""
        try:
            # Здесь можно добавить обработку задач из очереди Redis
            # Например:
            # - Отправка отложенных сообщений
            # - Обработка webhook-ов
            # - Генерация статистики
            # - Backup задачи
            
            logger.debug("🔄 Проверка фоновых задач...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки фоновых задач: {e}")
            
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        logger.info(f"📡 Получен сигнал {signum}, завершение работы...")
        self.is_running = False
        
    async def stop(self):
        """Остановка воркера"""
        logger.info("🛑 Остановка Background Worker...")
        self.is_running = False
        
        # Отменяем все задачи
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        logger.info("✅ Background Worker остановлен") 