#!/usr/bin/env python3
"""
Скрипт для принудительного применения SQL изменений для полей FAL AI.

Выполняет SQL команды напрямую, минуя Alembic, для добавления полей FAL AI.
"""
import asyncio
import asyncpg
import sys
from pathlib import Path

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

class DirectSQLMigrator:
    """Класс для прямого применения SQL миграций"""
    
    def __init__(self):
        self.db_connection = None
        
    async def connect_db(self):
        """Подключение к базе данных"""
        self.db_connection = await asyncpg.connect(
            settings.DATABASE_URL.replace('+asyncpg', '')
        )
    
    async def disconnect_db(self):
        """Отключение от базы данных"""
        if self.db_connection:
            await self.db_connection.close()
    
    async def check_current_state(self):
        """Проверяет текущее состояние таблицы avatars"""
        print("🔍 Проверка текущего состояния таблицы avatars...")
        
        columns = await self.db_connection.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'avatars' 
            ORDER BY ordinal_position
        """)
        
        existing_columns = [col['column_name'] for col in columns]
        
        fal_fields = [
            'training_type', 'fal_request_id', 'learning_rate', 
            'trigger_phrase', 'steps', 'multiresolution_training',
            'subject_crop', 'create_masks', 'captioning',
            'finetune_type', 'finetune_comment', 'diffusers_lora_file_url',
            'config_file_url', 'training_logs', 'training_error', 
            'webhook_url', 'last_status_check', 'fal_response_data'
        ]
        
        existing_fal = [f for f in fal_fields if f in existing_columns]
        missing_fal = [f for f in fal_fields if f not in existing_columns]
        
        print(f"   📊 Всего полей в avatars: {len(existing_columns)}")
        print(f"   ✅ Существующие FAL поля ({len(existing_fal)}): {existing_fal}")
        print(f"   ❌ Отсутствующие FAL поля ({len(missing_fal)}): {missing_fal}")
        
        return missing_fal
    
    async def create_enum_types(self):
        """Создает enum типы для FAL AI"""
        print("🏷️  Создание enum типов...")
        
        enum_commands = [
            """
            DO $$ BEGIN
                CREATE TYPE avatartrainingtype AS ENUM ('portrait', 'style');
            EXCEPTION
                WHEN duplicate_object THEN 
                    RAISE NOTICE 'Type avatartrainingtype already exists';
            END $$;
            """,
            """
            DO $$ BEGIN
                CREATE TYPE falfinetunetype AS ENUM ('full', 'lora');
            EXCEPTION
                WHEN duplicate_object THEN 
                    RAISE NOTICE 'Type falfinetunetype already exists';
            END $$;
            """,
            """
            DO $$ BEGIN
                CREATE TYPE falpriority AS ENUM ('speed', 'quality', 'high_res_only');
            EXCEPTION
                WHEN duplicate_object THEN 
                    RAISE NOTICE 'Type falpriority already exists';
            END $$;
            """
        ]
        
        for i, command in enumerate(enum_commands, 1):
            try:
                await self.db_connection.execute(command)
                print(f"   ✅ Enum тип {i}/3 создан/проверен")
            except Exception as e:
                print(f"   ❌ Ошибка создания enum типа {i}: {e}")
    
    async def add_fal_fields(self, missing_fields):
        """Добавляет отсутствующие поля FAL AI"""
        print(f"🔧 Добавление {len(missing_fields)} полей FAL AI...")
        
        # Карта полей и их типов
        field_definitions = {
            'training_type': 'avatartrainingtype DEFAULT \'portrait\'',
            'fal_request_id': 'VARCHAR(255)',
            'learning_rate': 'FLOAT',
            'trigger_phrase': 'VARCHAR(100)',
            'steps': 'INTEGER',
            'multiresolution_training': 'BOOLEAN DEFAULT true',
            'subject_crop': 'BOOLEAN DEFAULT true',
            'create_masks': 'BOOLEAN DEFAULT false',
            'captioning': 'BOOLEAN DEFAULT true',
            'finetune_type': 'falfinetunetype DEFAULT \'lora\'',
            'finetune_comment': 'VARCHAR(255)',
            'diffusers_lora_file_url': 'VARCHAR(500)',
            'config_file_url': 'VARCHAR(500)',
            'training_logs': 'TEXT',
            'training_error': 'TEXT',
            'webhook_url': 'VARCHAR(500)',
            'last_status_check': 'TIMESTAMP WITH TIME ZONE',
            'fal_response_data': 'JSON DEFAULT \'{}\'::json'
        }
        
        added_count = 0
        for field in missing_fields:
            if field in field_definitions:
                field_def = field_definitions[field]
                sql = f"ALTER TABLE avatars ADD COLUMN {field} {field_def};"
                
                try:
                    await self.db_connection.execute(sql)
                    print(f"   ✅ Добавлено поле: {field}")
                    added_count += 1
                except Exception as e:
                    print(f"   ❌ Ошибка добавления {field}: {e}")
            else:
                print(f"   ⚠️  Неизвестное поле: {field}")
        
        print(f"   📈 Успешно добавлено: {added_count}/{len(missing_fields)} полей")
        return added_count > 0
    
    async def create_indexes(self):
        """Создает индексы для новых полей"""
        print("📑 Создание индексов...")
        
        index_commands = [
            "CREATE INDEX IF NOT EXISTS ix_avatars_fal_request_id ON avatars (fal_request_id);",
            "CREATE INDEX IF NOT EXISTS ix_avatars_training_type ON avatars (training_type);",
        ]
        
        for command in index_commands:
            try:
                await self.db_connection.execute(command)
                print(f"   ✅ Индекс создан")
            except Exception as e:
                print(f"   ❌ Ошибка создания индекса: {e}")
    
    async def create_alembic_version_table(self):
        """Создает таблицу alembic_version"""
        print("🔧 Создание таблицы alembic_version...")
        
        try:
            # Создаем таблицу alembic_version
            await self.db_connection.execute("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """)
            
            # Получаем ID последней миграции из файла
            migration_files = list((project_root / "alembic" / "versions").glob("*.py"))
            if migration_files:
                latest_file = max(migration_files, key=lambda x: x.name)
                # Извлекаем ID из имени файла (формат: timestamp_id_description.py)
                migration_id = latest_file.stem.split('_')[2]
                
                # Вставляем версию
                await self.db_connection.execute(
                    "INSERT INTO alembic_version (version_num) VALUES ($1) ON CONFLICT DO NOTHING",
                    migration_id
                )
                
                print(f"   ✅ Таблица alembic_version создана с версией: {migration_id}")
            else:
                print("   ⚠️  Файлы миграций не найдены")
                
        except Exception as e:
            print(f"   ❌ Ошибка создания alembic_version: {e}")
    
    async def verify_final_state(self):
        """Проверяет итоговое состояние"""
        print("🎯 Проверка итогового состояния...")
        
        # Проверяем alembic_version
        try:
            version = await self.db_connection.fetchval('SELECT version_num FROM alembic_version')
            print(f"   ✅ Alembic версия: {version}")
        except Exception:
            print("   ❌ Таблица alembic_version не найдена")
        
        # Проверяем поля avatars
        missing_fields = await self.check_current_state()
        
        if not missing_fields:
            print("   🎉 Все поля FAL AI добавлены!")
            return True
        else:
            print(f"   ⚠️  Остались проблемы с {len(missing_fields)} полями")
            return False
    
    async def run_force_migration(self):
        """Выполняет принудительную миграцию"""
        print("="*60)
        print("🚀 ПРИНУДИТЕЛЬНОЕ ПРИМЕНЕНИЕ FAL AI ПОЛЕЙ")
        print("="*60)
        
        await self.connect_db()
        
        try:
            # Шаг 1: Проверяем текущее состояние
            missing_fields = await self.check_current_state()
            print()
            
            if not missing_fields:
                print("✅ Все поля FAL AI уже существуют!")
                return True
            
            # Шаг 2: Создаем enum типы
            await self.create_enum_types()
            print()
            
            # Шаг 3: Добавляем поля
            success = await self.add_fal_fields(missing_fields)
            print()
            
            if success:
                # Шаг 4: Создаем индексы
                await self.create_indexes()
                print()
                
                # Шаг 5: Создаем alembic_version
                await self.create_alembic_version_table()
                print()
            
            # Шаг 6: Финальная проверка
            final_success = await self.verify_final_state()
            print()
            
            if final_success:
                print("🎉 Принудительная миграция завершена успешно!")
            else:
                print("⚠️  Миграция завершена с предупреждениями")
            
            return final_success
            
        finally:
            await self.disconnect_db()

async def main():
    """Главная функция"""
    migrator = DirectSQLMigrator()
    await migrator.run_force_migration()

if __name__ == "__main__":
    asyncio.run(main()) 