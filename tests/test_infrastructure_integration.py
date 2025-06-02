#!/usr/bin/env python3
"""
Интеграционные тесты инфраструктуры
Тестирует PostgreSQL, Redis, MinIO
"""
import asyncio
import tempfile
import uuid
from datetime import datetime
from typing import Optional
import pytest
import aiofiles
import asyncpg
from minio import Minio
from minio.error import S3Error
import redis.asyncio as redis

from app.core.config import settings
from app.database.models import User, Avatar, AvatarTrainingType, AvatarGender
from app.core.database import get_session
from app.services.avatar.redis_service import AvatarRedisServiceclass TestDatabaseIntegration:
    """Тесты интеграции с PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Тест подключения к PostgreSQL"""
        try:
            # Прямое подключение к базе
            conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""))
            
            # Выполняем простой запрос
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            # Проверяем версию PostgreSQL
            version = await conn.fetchval("SELECT version()")
            print(f"✅ PostgreSQL версия: {version[:50]}...")
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"❌ Ошибка подключения к PostgreSQL: {e}")
    
    @pytest.mark.asyncio
    async def test_user_crud_operations(self):
        """Тест CRUD операций с пользователями"""
        async with get_session() as session:
            try:
                # Создание пользователя
                test_user_id = str(uuid.uuid4())
                user = User(
                    telegram_id=test_user_id,
                    first_name="Test",
                    last_name="User",
                    username="testuser",
                    language_code="ru"
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                print(f"✅ Пользователь создан: {user.id}")
                
                # Чтение пользователя
                found_user = await session.get(User, user.id)
                assert found_user is not None
                assert found_user.telegram_id == test_user_id
                assert found_user.first_name == "Test"
                
                # Обновление пользователя
                found_user.first_name = "Updated Test"
                await session.commit()
                await session.refresh(found_user)
                
                assert found_user.first_name == "Updated Test"
                print(f"✅ Пользователь обновлен")
                
                # Удаление пользователя
                await session.delete(found_user)
                await session.commit()
                
                deleted_user = await session.get(User, user.id)
                assert deleted_user is None
                print(f"✅ Пользователь удален")
                
            except Exception as e:
                await session.rollback()
                pytest.fail(f"❌ Ошибка CRUD операций: {e}")
    
    @pytest.mark.asyncio
    async def test_avatar_with_new_fields(self):
        """Тест создания аватара с новыми полями FAL AI"""
        async with get_session() as session:
            try:
                # Создаем пользователя
                user = User(
                    telegram_id=str(uuid.uuid4()),
                    first_name="Avatar",
                    last_name="Tester"
                )
                session.add(user)
                await session.flush()  # Чтобы получить user.id
                
                # Создаем аватар с новыми полями
                avatar = Avatar(
                    user_id=user.id,
                    name="Test Avatar",
                    gender=AvatarGender.MALE,
                    training_type=AvatarTrainingType.PORTRAIT,
                    
                    # FAL AI поля
                    fal_request_id="test_request_123",
                    learning_rate=0.0002,
                    trigger_phrase="TOK_test",
                    steps=1000,
                    multiresolution_training=True,
                    subject_crop=True,
                    create_masks=False,
                    captioning=True,
                    
                    # Результаты
                    diffusers_lora_file_url="https://test.com/lora.safetensors",
                    config_file_url="https://test.com/config.json",
                    training_logs="Training completed successfully",
                    
                    # Webhook
                    webhook_url="https://test.com/webhook",
                    last_status_check=datetime.utcnow()
                )
                
                session.add(avatar)
                await session.commit()
                await session.refresh(avatar)
                
                print(f"✅ Аватар создан с ID: {avatar.id}")
                
                # Проверяем новые поля
                assert avatar.training_type == AvatarTrainingType.PORTRAIT
                assert avatar.fal_request_id == "test_request_123"
                assert avatar.learning_rate == 0.0002
                assert avatar.trigger_phrase == "TOK_test"
                assert avatar.steps == 1000
                assert avatar.multiresolution_training is True
                assert avatar.subject_crop is True
                assert avatar.create_masks is False
                assert avatar.captioning is True
                assert avatar.diffusers_lora_file_url == "https://test.com/lora.safetensors"
                
                print(f"✅ Все новые поля аватара сохранены корректно")
                
                # Очистка
                await session.delete(avatar)
                await session.delete(user)
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                pytest.fail(f"❌ Ошибка создания аватара: {e}")class TestRedisIntegration:
    """Тесты интеграции с Redis"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Тест подключения к Redis"""
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # Проверяем соединение
            await redis_client.ping()
            print("✅ Redis подключение установлено")
            
            # Тест базовых операций
            test_key = f"test:{uuid.uuid4()}"
            await redis_client.set(test_key, "test_value", ex=60)
            
            value = await redis_client.get(test_key)
            assert value == b"test_value"
            
            await redis_client.delete(test_key)
            print("✅ Redis базовые операции работают")
            
            await redis_client.close()
            
        except Exception as e:
            pytest.fail(f"❌ Ошибка подключения к Redis: {e}")
    
    @pytest.mark.asyncio
    async def test_avatar_redis_service(self):
        """Тест сервиса Redis для аватаров"""
        try:
            service = AvatarRedisService()
            test_user_id = 12345
            
            # Тест буферизации фото
            photo_data = b"fake_photo_data_for_testing"
            photo_meta = {
                "file_id": "test_file_123",
                "width": 512,
                "height": 512,
                "format": "jpg"
            }
            
            # Буферизация
            success = await service.buffer_photo(test_user_id, photo_data, photo_meta)
            assert success is True
            print("✅ Фото буферизировано")
            
            # Получение информации о буфере
            buffer_info = await service.get_buffer_info(test_user_id)
            assert buffer_info["count"] == 1
            assert buffer_info["total_size"] > 0
            print(f"✅ Информация о буфере: {buffer_info}")
            
            # Получение фото
            photos = await service.get_buffered_photos(test_user_id)
            assert len(photos) == 1
            assert photos[0]["data"] == photo_data
            assert photos[0]["metadata"]["file_id"] == "test_file_123"
            print("✅ Фото получено из буфера")
            
            # Тест блокировок
            lock_token = await service.acquire_avatar_lock(test_user_id, "create")
            assert lock_token is not None
            print(f"✅ Блокировка получена: {lock_token}")
            
            # Проверяем что повторная блокировка не работает
            second_lock = await service.acquire_avatar_lock(test_user_id, "create")
            assert second_lock is None
            print("✅ Повторная блокировка заблокирована")
            
            # Освобождение блокировки
            released = await service.release_avatar_lock(test_user_id, lock_token, "create")
            assert released is True
            print("✅ Блокировка освобождена")
            
            # Очистка
            await service.clear_photo_buffer(test_user_id)
            await service.close()
            
        except Exception as e:
            pytest.fail(f"❌ Ошибка сервиса Redis: {e}")class TestMinIOIntegration:
    """Тесты интеграции с MinIO"""
    
    def setup_minio_client(self) -> Optional[Minio]:
        """Настройка клиента MinIO"""
        try:
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            return client
        except Exception as e:
            print(f"❌ Ошибка настройки MinIO клиента: {e}")
            return None
    
    @pytest.mark.asyncio
    async def test_minio_connection(self):
        """Тест подключения к MinIO"""
        client = self.setup_minio_client()
        if not client:
            pytest.skip("MinIO клиент не настроен")
        
        try:
            # Проверяем доступность сервера
            buckets = client.list_buckets()
            print(f"✅ MinIO доступен, бакетов: {len(buckets)}")
            
            # Проверяем основной бакет аватаров
            bucket_name = settings.MINIO_BUCKET_AVATARS
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"✅ Бакет {bucket_name} создан")
            else:
                print(f"✅ Бакет {bucket_name} существует")
                
        except Exception as e:
            pytest.fail(f"❌ Ошибка подключения к MinIO: {e}")
    
    @pytest.mark.asyncio
    async def test_minio_file_operations(self):
        """Тест операций с файлами в MinIO"""
        client = self.setup_minio_client()
        if not client:
            pytest.skip("MinIO клиент не настроен")
        
        try:
            bucket_name = settings.MINIO_BUCKET_AVATARS
            
            # Создаем тестовый файл
            test_content = b"Test file content for avatar photo"
            test_filename = f"test/{uuid.uuid4()}.jpg"
            
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(test_content)
                tmp_file.flush()
                
                # Загрузка файла
                client.fput_object(bucket_name, test_filename, tmp_file.name)
                print(f"✅ Файл загружен: {test_filename}")
            
            # Проверяем что файл существует
            try:
                stat = client.stat_object(bucket_name, test_filename)
                assert stat.size == len(test_content)
                print(f"✅ Файл найден, размер: {stat.size} байт")
            except S3Error:
                pytest.fail("Файл не найден после загрузки")
            
            # Скачивание файла
            with tempfile.NamedTemporaryFile() as download_file:
                client.fget_object(bucket_name, test_filename, download_file.name)
                
                # Проверяем содержимое
                with open(download_file.name, 'rb') as f:
                    downloaded_content = f.read()
                
                assert downloaded_content == test_content
                print("✅ Файл скачан и содержимое совпадает")
            
            # Получение URL файла
            url = client.presigned_get_object(bucket_name, test_filename, expires=3600)
            assert url.startswith('http')
            print(f"✅ Presigned URL получен: {url[:50]}...")
            
            # Удаление файла
            client.remove_object(bucket_name, test_filename)
            print("✅ Файл удален")
            
            # Проверяем что файл удален
            try:
                client.stat_object(bucket_name, test_filename)
                pytest.fail("Файл не был удален")
            except S3Error:
                print("✅ Файл действительно удален")
                
        except Exception as e:
            pytest.fail(f"❌ Ошибка операций с файлами MinIO: {e}")class TestFullIntegration:
    """Комплексные интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_avatar_creation_workflow(self):
        """Тест полного процесса создания аватара с использованием всех сервисов"""
        
        # 1. Создаем пользователя в PostgreSQL
        async with get_session() as session:
            user = User(
                telegram_id=str(uuid.uuid4()),
                first_name="Integration",
                last_name="Test"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✅ Пользователь создан: {user.id}")
        
        try:
            # 2. Буферизируем фото в Redis
            redis_service = AvatarRedisService()
            user_telegram_id = int(user.telegram_id) if user.telegram_id.isdigit() else 12345
            
            photo_data = b"test_photo_data_for_integration"
            photo_meta = {"file_id": "integration_test", "width": 512, "height": 512}
            
            success = await redis_service.buffer_photo(user_telegram_id, photo_data, photo_meta)
            assert success is True
            print("✅ Фото буферизировано в Redis")
            
            # 3. Создаем аватар в PostgreSQL
            async with get_session() as session:
                avatar = Avatar(
                    user_id=user.id,
                    name="Integration Test Avatar",
                    gender=AvatarGender.MALE,
                    training_type=AvatarTrainingType.PORTRAIT,
                    fal_request_id="integration_test_123",
                    learning_rate=0.0002
                )
                session.add(avatar)
                await session.commit()
                await session.refresh(avatar)
                print(f"✅ Аватар создан: {avatar.id}")
            
            # 4. Тестируем MinIO (если доступен)
            minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            ) if hasattr(settings, 'MINIO_ENDPOINT') else None
            
            if minio_client:
                try:
                    bucket_name = getattr(settings, 'MINIO_BUCKET_AVATARS', 'avatars')
                    test_key = f"avatars/{avatar.id}/test_photo.jpg"
                    
                    with tempfile.NamedTemporaryFile() as tmp_file:
                        tmp_file.write(photo_data)
                        tmp_file.flush()
                        
                        minio_client.fput_object(bucket_name, test_key, tmp_file.name)
                        print(f"✅ Фото сохранено в MinIO: {test_key}")
                        
                        # Удаляем тестовый файл
                        minio_client.remove_object(bucket_name, test_key)
                        
                except Exception as minio_error:
                    print(f"⚠️ MinIO не доступен или настроен: {minio_error}")
            
            # 5. Проверяем что все данные связаны корректно
            async with get_session() as session:
                # Получаем пользователя с аватарами
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload
                
                result = await session.execute(
                    select(User).options(selectinload(User.avatars)).where(User.id == user.id)
                )
                found_user = result.scalar_one_or_none()
                
                assert found_user is not None
                assert len(found_user.avatars) == 1
                assert found_user.avatars[0].id == avatar.id
                assert found_user.avatars[0].training_type == AvatarTrainingType.PORTRAIT
                
                print("✅ Связи между сущностями корректны")
            
            # 6. Получаем данные из Redis
            buffered_photos = await redis_service.get_buffered_photos(user_telegram_id)
            assert len(buffered_photos) == 1
            assert buffered_photos[0]["data"] == photo_data
            
            print("✅ Полный интеграционный тест прошел успешно!")
            
        finally:
            # Очистка
            try:
                await redis_service.clear_photo_buffer(user_telegram_id)
                await redis_service.close()
                
                async with get_session() as session:
                    # Удаляем аватар и пользователя
                    found_avatar = await session.get(Avatar, avatar.id)
                    if found_avatar:
                        await session.delete(found_avatar)
                    
                    found_user = await session.get(User, user.id)
                    if found_user:
                        await session.delete(found_user)
                    
                    await session.commit()
                    
                print("✅ Очистка выполнена")
                
            except Exception as cleanup_error:
                print(f"⚠️ Ошибка очистки: {cleanup_error}")# Вспомогательные функции для запуска тестов
if __name__ == "__main__":
    async def run_tests():
        """Запуск всех тестов"""
        print("🚀 Запуск интеграционных тестов инфраструктуры\n")
        
        test_classes = [
            TestDatabaseIntegration(),
            TestRedisIntegration(), 
            TestMinIOIntegration(),
            TestFullIntegration()
        ]
        
        for test_instance in test_classes:
            class_name = test_instance.__class__.__name__
            print(f"\n{'='*60}")
            print(f"🧪 ТЕСТЫ: {class_name}")
            print('='*60)
            
            # Получаем все методы тестов
            test_methods = [method for method in dir(test_instance) 
                          if method.startswith('test_') and callable(getattr(test_instance, method))]
            
            for test_method_name in test_methods:
                try:
                    print(f"\n🔍 Запуск: {test_method_name}")
                    test_method = getattr(test_instance, test_method_name)
                    await test_method()
                    print(f"✅ {test_method_name} - ПРОШЕЛ")
                    
                except Exception as e:
                    print(f"❌ {test_method_name} - ПРОВАЛЕН: {e}")
        
        print(f"\n{'='*60}")
        print("🎉 Интеграционные тесты завершены")
        print('='*60)
    
    # Запуск тестов
    asyncio.run(run_tests())
