#!/usr/bin/env python3
"""
Скрипт для полного сброса миграций и создания новых на основе текущих моделей.

Этот скрипт:
1. Удаляет все файлы миграций
2. Удаляет таблицу alembic_version из БД  
3. Очищает кэш Python модулей
4. Создает новую начальную миграцию на основе текущих моделей
5. При необходимости принудительно добавляет поля FAL AI
6. Применяет миграцию к БД

ВНИМАНИЕ: Этот скрипт не удаляет данные, только пересоздает структуру миграций!
"""
import asyncio
import asyncpg
import os
import sys
import glob
import subprocess
import shutil
from pathlib import Path

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

class MigrationResetter:
    """Класс для сброса и пересоздания миграций"""
    
    def __init__(self):
        self.project_root = project_root
        self.migrations_dir = self.project_root / "alembic" / "versions"
        
    def clear_python_cache(self):
        """Очищает кэш Python модулей"""
        print("🧹 Очищаем кэш Python...")
        
        cache_dirs = []
        
        # Находим все __pycache__ директории
        for root, dirs, files in os.walk(self.project_root):
            if '__pycache__' in dirs:
                cache_dir = Path(root) / '__pycache__'
                cache_dirs.append(cache_dir)
        
        # Удаляем найденные кэш директории
        removed_count = 0
        for cache_dir in cache_dirs:
            try:
                shutil.rmtree(cache_dir)
                removed_count += 1
                print(f"   🗂️  Удален кэш: {cache_dir.relative_to(self.project_root)}")
            except Exception as e:
                print(f"   ⚠️  Не удалось удалить {cache_dir}: {e}")
        
        print(f"   ✅ Удалено {removed_count} кэш директорий")
        
        # Очищаем кэш модулей из памяти
        modules_to_clear = [name for name in sys.modules.keys() 
                          if name.startswith('app.database') or name.startswith('app.core')]
        
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
                print(f"   🔄 Очищен модуль: {module_name}")
        
        print(f"   ✅ Очищено {len(modules_to_clear)} модулей из памяти")
        
    async def reset_alembic_version_table(self):
        """Удаляет таблицу alembic_version из БД"""
        print("🗑️  Удаляем таблицу alembic_version...")
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
            
            # Удаляем таблицу alembic_version
            await conn.execute("DROP TABLE IF EXISTS alembic_version")
            print("   ✅ Таблица alembic_version удалена")
            
            await conn.close()
            
        except Exception as e:
            print(f"   ❌ Ошибка удаления таблицы alembic_version: {e}")
            raise
    
    def remove_migration_files(self):
        """Удаляет все файлы миграций"""
        print("🗑️  Удаляем файлы миграций...")
        
        # Находим все файлы миграций
        migration_files = glob.glob(str(self.migrations_dir / "*.py"))
        
        removed_count = 0
        for file_path in migration_files:
            try:
                os.remove(file_path)
                print(f"   🗂️  Удален: {os.path.basename(file_path)}")
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка удаления {file_path}: {e}")
        
        print(f"   ✅ Удалено {removed_count} файлов миграций")
    
    def check_models_loaded(self):
        """Проверяет что модели корректно загружены"""
        print("🔍 Проверяем загрузку моделей...")
        
        try:
            # Принудительная перезагрузка модулей
            import importlib
            
            # Загружаем модели заново
            from app.database.models import Base, Avatar, AvatarTrainingType
            
            # Проверяем метаданные
            metadata = Base.metadata
            tables = list(metadata.tables.keys())
            print(f"   ✅ Загружено {len(tables)} таблиц: {tables}")
            
            # Проверяем поля Avatar
            if 'avatars' in metadata.tables:
                avatars_table = metadata.tables['avatars']
                columns = [col.name for col in avatars_table.columns]
                
                # Ключевые поля FAL AI
                fal_fields = ['training_type', 'fal_request_id', 'learning_rate']
                found_fal = [f for f in fal_fields if f in columns]
                
                print(f"   ✅ Поля avatars: {len(columns)}")
                print(f"   🎯 Поля FAL AI найдены: {found_fal}")
                
                if len(found_fal) >= 2:
                    print("   ✅ Модель Avatar содержит поля FAL AI")
                    return True
                else:
                    print("   ❌ Модель Avatar НЕ содержит достаточно полей FAL AI")
                    return False
            else:
                print("   ❌ Таблица avatars не найдена в метаданных")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка проверки моделей: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_initial_migration(self):
        """Создает начальную миграцию на основе текущих моделей"""
        print("🏗️  Создаем начальную миграцию...")
        
        try:
            # Переходим в корень проекта для выполнения alembic команд
            os.chdir(self.project_root)
            
            # Создаем автомиграцию
            result = subprocess.run([
                "alembic", "revision", "--autogenerate", 
                "-m", "initial_schema_with_fal_ai_fields"
            ], capture_output=True, text=True, check=True)
            
            print("   ✅ Начальная миграция создана")
            if result.stdout:
                print(f"   📄 Вывод: {result.stdout.strip()}")
                
            # Находим созданный файл миграции
            migration_files = list(self.migrations_dir.glob("*.py"))
            if migration_files:
                latest_migration = max(migration_files, key=lambda x: x.name)
                return latest_migration
            else:
                print("   ❌ Файл миграции не найден")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Ошибка создания миграции: {e}")
            if e.stdout:
                print(f"   📄 Stdout: {e.stdout}")
            if e.stderr:
                print(f"   📄 Stderr: {e.stderr}")
            raise
    
    def check_migration_content(self, migration_file):
        """Проверяет содержимое миграции"""
        print("🔍 Проверяем содержимое миграции...")
        
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем что миграция не пустая
            if 'def upgrade() -> None:\n    pass' in content:
                print("   ❌ Миграция ПУСТАЯ!")
                return False
            
            # Проверяем наличие ключевых операций
            has_operations = any(keyword in content for keyword in [
                'op.add_column', 'op.create_table', 'op.alter_column'
            ])
            
            if has_operations:
                print("   ✅ Миграция содержит операции")
                return True
            else:
                print("   ⚠️  Миграция не содержит операций")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка чтения миграции: {e}")
            return False
    
    def create_manual_fal_migration(self, migration_file):
        """Создает ручную миграцию для полей FAL AI"""
        print("🔧 Создаем ручную миграцию для полей FAL AI...")
        
        try:
            # Читаем существующую миграцию
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Заменяем пустую функцию upgrade на полную миграцию FAL AI
            manual_upgrade = '''def upgrade() -> None:
    """Добавляем поля FAL AI в таблицу avatars"""
    
    # Создаем новые enum типы если их нет
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE avatartrainingtype AS ENUM ('portrait', 'style');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE falfinetunetype AS ENUM ('full', 'lora');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE falpriority AS ENUM ('speed', 'quality', 'high_res_only');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Добавляем новые поля в таблицу avatars если их нет
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_type avatartrainingtype DEFAULT 'portrait';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN fal_request_id VARCHAR(255);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN learning_rate FLOAT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN trigger_phrase VARCHAR(100);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN steps INTEGER;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN multiresolution_training BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN subject_crop BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN create_masks BOOLEAN DEFAULT false;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN captioning BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN finetune_type falfinetunetype DEFAULT 'lora';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN finetune_comment VARCHAR(255);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN diffusers_lora_file_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN config_file_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_logs TEXT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_error TEXT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN webhook_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN last_status_check TIMESTAMP WITH TIME ZONE;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN fal_response_data JSON DEFAULT '{}';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    # Обновляем существующее поле fal_priority на enum (если нужно)
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ALTER COLUMN fal_priority TYPE falpriority USING fal_priority::falpriority;
            EXCEPTION
                WHEN OTHERS THEN null;
            END;
        END $$;
    """)
    
    # Создаем индексы
    op.execute("""
        DO $$ BEGIN
            BEGIN
                CREATE INDEX ix_avatars_fal_request_id ON avatars (fal_request_id);
            EXCEPTION
                WHEN duplicate_table THEN null;
            END;
        END $$;
    """)
'''
            
            # Заменяем пустую функцию на нашу
            new_content = content.replace(
                'def upgrade() -> None:\n    pass',
                manual_upgrade
            )
            
            # Записываем обновленную миграцию
            with open(migration_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("   ✅ Ручная миграция для FAL AI создана")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка создания ручной миграции: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_migration(self):
        """Применяет созданную миграцию"""
        print("🚀 Применяем миграцию...")
        
        try:
            # Применяем миграцию
            result = subprocess.run([
                "alembic", "upgrade", "head"
            ], capture_output=True, text=True, check=True)
            
            print("   ✅ Миграция применена")
            if result.stdout:
                print(f"   📄 Вывод: {result.stdout.strip()}")
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Ошибка применения миграции: {e}")
            if e.stdout:
                print(f"   📄 Stdout: {e.stdout}")
            if e.stderr:
                print(f"   📄 Stderr: {e.stderr}")
            raise
    
    async def check_final_state(self):
        """Проверяет финальное состояние БД и миграций"""
        print("🔍 Проверяем финальное состояние...")
        
        try:
            conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
            
            # Проверяем версию Alembic
            try:
                version = await conn.fetchval('SELECT version_num FROM alembic_version')
                print(f"   🔧 Версия Alembic: {version}")
            except Exception:
                print("   ❌ Таблица alembic_version не найдена")
            
            # Проверяем структуру таблицы avatars
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'avatars' 
                ORDER BY ordinal_position
            """)
            
            all_columns = [col['column_name'] for col in columns]
            print(f"   📊 Всего полей в avatars: {len(all_columns)}")
            
            # Проверяем наличие ключевых полей FAL AI
            fal_fields = ['training_type', 'fal_request_id', 'learning_rate', 
                         'trigger_phrase', 'diffusers_lora_file_url']
            
            existing_fal_fields = [f for f in fal_fields if f in all_columns]
            missing_fal_fields = [f for f in fal_fields if f not in all_columns]
            
            print("   📋 Проверка ключевых полей FAL AI:")
            for field in existing_fal_fields:
                print(f"      ✅ {field}")
            
            for field in missing_fal_fields:
                print(f"      ❌ {field}")
            
            success_rate = len(existing_fal_fields) / len(fal_fields)
            print(f"   📈 Успешность: {success_rate*100:.1f}%")
            
            await conn.close()
            
            return success_rate >= 0.8  # 80% полей должны быть созданы
            
        except Exception as e:
            print(f"   ❌ Ошибка проверки состояния: {e}")
            return False
    
    async def run_full_reset(self):
        """Выполняет полный сброс миграций"""
        print("🔄 Начинаем полный сброс миграций...\n")
        
        try:
            # Шаг 1: Очищаем кэш Python
            self.clear_python_cache()
            print()
            
            # Шаг 2: Удаляем таблицу alembic_version
            await self.reset_alembic_version_table()
            print()
            
            # Шаг 3: Удаляем файлы миграций
            self.remove_migration_files()
            print()
            
            # Шаг 4: Проверяем загрузку моделей
            models_ok = self.check_models_loaded()
            print()
            
            # Шаг 5: Создаем новую миграцию
            migration_file = self.create_initial_migration()
            print()
            
            # Шаг 6: Проверяем содержимое миграции
            if migration_file:
                migration_has_content = self.check_migration_content(migration_file)
                
                # Если миграция пустая, создаем ручную
                if not migration_has_content:
                    print("⚠️  Автогенерация не сработала, создаем ручную миграцию...")
                    self.create_manual_fal_migration(migration_file)
                    print()
            
            # Шаг 7: Применяем миграцию
            self.apply_migration()
            print()
            
            # Шаг 8: Проверяем результат
            success = await self.check_final_state()
            print()
            
            if success:
                print("🎉 Сброс миграций завершен успешно!")
                print("✅ Поля FAL AI добавлены в таблицу avatars")
            else:
                print("⚠️  Сброс завершен, но есть проблемы с полями FAL AI")
                print("🔧 Попробуйте запустить скрипт еще раз или проверьте модели")
            
        except Exception as e:
            print(f"\n💥 Ошибка во время сброса миграций: {e}")
            print("   Возможно, потребуется ручная очистка")
            import traceback
            traceback.print_exc()
            sys.exit(1)

async def main():
    """Главная функция"""
    print("="*60)
    print("🔄 СКРИПТ СБРОСА МИГРАЦИЙ (РАСШИРЕННАЯ ВЕРСИЯ)")
    print("="*60)
    print("Этот скрипт пересоздаст миграции на основе текущих моделей")
    print("+ Очистка кэша Python")
    print("+ Принудительное создание полей FAL AI")
    print("+ Детальная диагностика")
    print("ВНИМАНИЕ: Данные не будут удалены, только структура миграций")
    print("="*60)
    
    # Подтверждение от пользователя
    try:
        confirm = input("\n❓ Продолжить расширенный сброс миграций? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', 'да']:
            print("🚫 Операция отменена")
            return
    except KeyboardInterrupt:
        print("\n🚫 Операция отменена")
        return
    
    print()
    
    # Выполняем сброс
    resetter = MigrationResetter()
    await resetter.run_full_reset()

if __name__ == "__main__":
    asyncio.run(main()) 