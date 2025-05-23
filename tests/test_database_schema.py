#!/usr/bin/env python3
"""
Pytest тесты для проверки схемы базы данных и синхронизации миграций
"""
import pytest
import asyncpg
from typing import List, Set
import sys
from pathlib import Path

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.database.models import Base, Avatar

class TestDatabaseSchema:
    """Тесты схемы базы данных"""
    
    @pytest.fixture
    async def db_connection(self):
        """Фикстура подключения к БД"""
        conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
        yield conn
        await conn.close()
    
    async def test_alembic_version_exists(self, db_connection):
        """Проверяет что таблица alembic_version существует и содержит версию"""
        # Проверяем существование таблицы
        table_exists = await db_connection.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            )
        """)
        
        assert table_exists, "Таблица alembic_version не существует"
        
        # Проверяем наличие версии
        version = await db_connection.fetchval('SELECT version_num FROM alembic_version')
        assert version is not None, "Версия Alembic не установлена"
        assert len(version) > 0, "Версия Alembic пустая"
        
        print(f"✅ Alembic версия: {version}")
    
    async def test_required_tables_exist(self, db_connection):
        """Проверяет что все необходимые таблицы существуют"""
        expected_tables = {
            'users', 'user_balances', 'user_states', 'avatars', 
            'avatar_photos', 'user_transcripts', 'user_profiles',
            'user_transcript_cache', 'alembic_version'
        }
        
        # Получаем список таблиц из БД
        tables = await db_connection.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        existing_tables = {t['table_name'] for t in tables}
        
        missing_tables = expected_tables - existing_tables
        extra_tables = existing_tables - expected_tables
        
        assert not missing_tables, f"Отсутствуют таблицы: {missing_tables}"
        
        if extra_tables:
            print(f"⚠️ Дополнительные таблицы: {extra_tables}")
        
        print(f"✅ Все таблицы присутствуют: {len(existing_tables)}")
    
    async def test_avatar_table_structure(self, db_connection):
        """Проверяет структуру таблицы avatars"""
        # Получаем структуру таблицы
        columns = await db_connection.fetch("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'avatars' 
            ORDER BY ordinal_position
        """)
        
        column_names = {col['column_name'] for col in columns}
        
        # Базовые поля
        required_basic_fields = {
            'id', 'user_id', 'name', 'gender', 'avatar_type', 'status',
            'created_at', 'updated_at'
        }
        
        missing_basic = required_basic_fields - column_names
        assert not missing_basic, f"Отсутствуют базовые поля: {missing_basic}"
        
        print(f"✅ Базовые поля avatars: {len(required_basic_fields)}")
    
    async def test_avatar_fal_ai_fields(self, db_connection):
        """Проверяет наличие полей FAL AI в таблице avatars"""
        columns = await db_connection.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'avatars'
        """)
        
        column_names = {col['column_name'] for col in columns}
        
        # Поля FAL AI
        fal_ai_fields = {
            'training_type', 'fal_request_id', 'learning_rate', 
            'trigger_phrase', 'steps', 'multiresolution_training',
            'subject_crop', 'create_masks', 'captioning',
            'finetune_type', 'finetune_comment', 'diffusers_lora_file_url',
            'config_file_url', 'training_logs', 'training_error',
            'webhook_url', 'last_status_check', 'fal_response_data'
        }
        
        missing_fal_fields = fal_ai_fields - column_names
        existing_fal_fields = fal_ai_fields & column_names
        
        print(f"✅ Поля FAL AI найдены: {len(existing_fal_fields)}")
        if missing_fal_fields:
            print(f"❌ Отсутствуют поля FAL AI: {missing_fal_fields}")
            
        # Проверяем что большинство полей присутствует
        coverage = len(existing_fal_fields) / len(fal_ai_fields)
        assert coverage >= 0.8, f"Недостаточно полей FAL AI: {coverage*100:.1f}% покрытие"
    
    async def test_enum_types_exist(self, db_connection):
        """Проверяет что необходимые enum типы существуют"""
        # Получаем enum типы
        enum_types = await db_connection.fetch("""
            SELECT typname 
            FROM pg_type 
            WHERE typtype = 'e' 
            ORDER BY typname
        """)
        
        existing_enums = {e['typname'] for e in enum_types}
        
        # Ожидаемые enum типы
        expected_enums = {
            'avatargender', 'avatarstatus', 'avatartype', 
            'photovalidationstatus'
        }
        
        # Новые enum типы FAL AI (могут отсутствовать в старых версиях)
        fal_enums = {
            'avatartrainingtype', 'falfinetunetype', 'falpriority'
        }
        
        missing_basic_enums = expected_enums - existing_enums
        assert not missing_basic_enums, f"Отсутствуют базовые enum типы: {missing_basic_enums}"
        
        missing_fal_enums = fal_enums - existing_enums
        if missing_fal_enums:
            print(f"⚠️ Отсутствуют FAL AI enum типы: {missing_fal_enums}")
        
        print(f"✅ Enum типы: {existing_enums}")
    
    async def test_indexes_exist(self, db_connection):
        """Проверяет важные индексы"""
        indexes = await db_connection.fetch("""
            SELECT 
                schemaname, 
                tablename, 
                indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        index_names = {idx['indexname'] for idx in indexes}
        
        # Критически важные индексы
        critical_indexes = {
            'ix_users_telegram_id',  # Поиск пользователей по telegram_id
            'avatars_pkey',          # Primary key avatars
            'users_pkey'             # Primary key users
        }
        
        missing_critical = critical_indexes - index_names
        if missing_critical:
            print(f"⚠️ Отсутствуют критические индексы: {missing_critical}")
        
        print(f"✅ Всего индексов: {len(index_names)}")
    
    def test_models_metadata_consistency(self):
        """Проверяет что метаданные SQLAlchemy корректны"""
        # Проверяем что модели загружаются
        tables = Base.metadata.tables
        assert len(tables) > 0, "Не загружены таблицы из моделей"
        
        # Проверяем ключевые таблицы
        expected_model_tables = {'users', 'avatars', 'avatar_photos'}
        missing_models = expected_model_tables - set(tables.keys())
        assert not missing_models, f"Отсутствуют модели: {missing_models}"
        
        # Проверяем модель Avatar
        avatar_table = tables['avatars']
        avatar_columns = {col.name for col in avatar_table.columns}
        
        # Базовые поля модели Avatar
        required_avatar_fields = {'id', 'user_id', 'name', 'gender', 'status'}
        missing_avatar_fields = required_avatar_fields - avatar_columns
        assert not missing_avatar_fields, f"Отсутствуют поля в модели Avatar: {missing_avatar_fields}"
        
        print(f"✅ Модель Avatar содержит {len(avatar_columns)} полей")

class TestDatabaseIntegrity:
    """Тесты целостности данных"""
    
    @pytest.fixture
    async def db_connection(self):
        """Фикстура подключения к БД"""
        conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
        yield conn
        await conn.close()
    
    async def test_foreign_keys_exist(self, db_connection):
        """Проверяет что внешние ключи настроены"""
        foreign_keys = await db_connection.fetch("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        """)
        
        # Критически важные FK
        fk_map = {}
        for fk in foreign_keys:
            table = fk['table_name']
            if table not in fk_map:
                fk_map[table] = []
            fk_map[table].append(f"{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # Проверяем что аватары связаны с пользователями
        assert 'avatars' in fk_map, "Таблица avatars не имеет внешних ключей"
        avatar_fks = fk_map['avatars']
        user_fk_exists = any('users.id' in fk for fk in avatar_fks)
        assert user_fk_exists, "Связь avatars -> users отсутствует"
        
        print(f"✅ Внешние ключи: {len(foreign_keys)}")
    
    async def test_data_consistency(self, db_connection):
        """Базовая проверка целостности данных"""
        # Проверяем что нет пользователей без ID
        orphan_users = await db_connection.fetchval("""
            SELECT COUNT(*) FROM users WHERE id IS NULL
        """)
        assert orphan_users == 0, f"Найдены пользователи без ID: {orphan_users}"
        
        # Проверяем что нет аватаров без пользователей
        orphan_avatars = await db_connection.fetchval("""
            SELECT COUNT(*) 
            FROM avatars a 
            LEFT JOIN users u ON a.user_id = u.id 
            WHERE u.id IS NULL
        """)
        assert orphan_avatars == 0, f"Найдены аватары без пользователей: {orphan_avatars}"
        
        print(f"✅ Данные целостны")

if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v"]) 