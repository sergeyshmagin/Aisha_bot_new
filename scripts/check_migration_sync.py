#!/usr/bin/env python3
"""
Скрипт для проверки синхронизации между моделями SQLAlchemy и реальной структурой БД.

Сравнивает:
- Поля в моделях vs поля в БД
- Типы данных
- Ограничения и индексы
- Версии миграций
- Диагностика проблем с Alembic
"""
import asyncio
import asyncpg
import sys
import os
import importlib
from pathlib import Path
from typing import Dict, List, Set

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.database.models import Base, Avatar
import sqlalchemy as sa

class AlembicDiagnostics:
    """Класс для диагностики проблем с Alembic"""
    
    def __init__(self):
        self.project_root = project_root
        
    def check_alembic_configuration(self):
        """Проверяет конфигурацию Alembic"""
        print("\n🔧 Диагностика конфигурации Alembic:")
        print("-" * 50)
        
        # Проверяем alembic.ini
        alembic_ini = self.project_root / "alembic.ini"
        if alembic_ini.exists():
            print("✅ alembic.ini найден")
        else:
            print("❌ alembic.ini отсутствует")
            return False
        
        # Проверяем alembic/env.py
        env_py = self.project_root / "alembic" / "env.py"
        if env_py.exists():
            print("✅ alembic/env.py найден")
        else:
            print("❌ alembic/env.py отсутствует")
            return False
        
        # Проверяем содержимое env.py
        try:
            with open(env_py, 'r', encoding='utf-8') as f:
                env_content = f.read()
                
            if 'target_metadata = Base.metadata' in env_content:
                print("✅ target_metadata настроен")
            else:
                print("❌ target_metadata не настроен или настроен неправильно")
                
            if 'from app.database.models import Base' in env_content:
                print("✅ Импорт Base найден")
            else:
                print("❌ Импорт Base отсутствует")
                
        except Exception as e:
            print(f"❌ Ошибка чтения env.py: {e}")
            
        return True
    
    def check_sqlalchemy_metadata(self):
        """Проверяет метаданные SQLAlchemy"""
        print("\n📋 Диагностика метаданных SQLAlchemy:")
        print("-" * 50)
        
        try:
            # Проверяем загрузку базовых модулей
            print("🔍 Проверка импорта модулей...")
            
            # Импорт Base
            from app.database.models import Base
            print("✅ Base импортирован")
            
            # Проверяем метаданные
            metadata = Base.metadata
            print(f"✅ Метаданные получены: {len(metadata.tables)} таблиц")
            
            # Список таблиц в метаданных
            model_tables = list(metadata.tables.keys())
            print(f"📊 Таблицы в метаданных: {model_tables}")
            
            # Проверяем конкретно таблицу avatars
            if 'avatars' in metadata.tables:
                avatars_table = metadata.tables['avatars']
                columns = [col.name for col in avatars_table.columns]
                print(f"✅ Таблица avatars: {len(columns)} полей")
                
                # Проверяем новые поля FAL AI
                fal_fields = [
                    'training_type', 'fal_request_id', 'learning_rate', 
                    'trigger_phrase', 'steps', 'multiresolution_training',
                    'subject_crop', 'create_masks', 'captioning',
                    'finetune_type', 'finetune_comment'
                ]
                
                found_fal_fields = [f for f in fal_fields if f in columns]
                missing_fal_fields = [f for f in fal_fields if f not in columns]
                
                print(f"✅ Поля FAL AI в модели: {len(found_fal_fields)}/{len(fal_fields)}")
                if found_fal_fields:
                    print(f"   Найдены: {found_fal_fields}")
                if missing_fal_fields:
                    print(f"   Отсутствуют: {missing_fal_fields}")
                    
            else:
                print("❌ Таблица avatars не найдена в метаданных")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки метаданных: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_alembic_imports(self):
        """Проверяет что Alembic может импортировать модели"""
        print("\n🔄 Диагностика импорта в Alembic:")
        print("-" * 50)
        
        try:
            # Эмулируем импорт как в alembic/env.py
            old_path = sys.path.copy()
            
            # Добавляем пути как в env.py
            env_py_dir = self.project_root / "alembic"
            sys.path.insert(0, str(env_py_dir.parent))
            
            print("🔍 Эмуляция импорта из alembic/env.py...")
            
            # Пробуем импортировать как в env.py
            from app.core.config import settings as alembic_settings
            print("✅ app.core.config импортирован")
            
            from app.database.models import Base as alembic_base
            print("✅ app.database.models.Base импортирован")
            
            # Проверяем метаданные в контексте Alembic
            alembic_metadata = alembic_base.metadata
            alembic_tables = list(alembic_metadata.tables.keys())
            print(f"✅ Метаданные в Alembic: {len(alembic_tables)} таблиц")
            
            if 'avatars' in alembic_metadata.tables:
                avatars_cols = [col.name for col in alembic_metadata.tables['avatars'].columns]
                print(f"✅ Поля avatars в Alembic: {len(avatars_cols)}")
                
                # Проверяем FAL AI поля
                fal_in_alembic = [f for f in ['training_type', 'fal_request_id'] if f in avatars_cols]
                print(f"🔍 FAL AI поля в Alembic: {fal_in_alembic}")
            
            sys.path = old_path
            return True
            
        except Exception as e:
            sys.path = old_path
            print(f"❌ Ошибка импорта в Alembic: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_enum_registration(self):
        """Проверяет регистрацию enum типов"""
        print("\n🏷️  Диагностика enum типов:")
        print("-" * 50)
        
        try:
            from app.database.models import (
                AvatarTrainingType, FALFinetuneType, FALPriority
            )
            
            print("✅ Enum типы импортированы")
            
            # Проверяем значения
            training_types = list(AvatarTrainingType)
            print(f"✅ AvatarTrainingType: {[t.value for t in training_types]}")
            
            finetune_types = list(FALFinetuneType)
            print(f"✅ FALFinetuneType: {[t.value for t in finetune_types]}")
            
            priorities = list(FALPriority)
            print(f"✅ FALPriority: {[p.value for p in priorities]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки enum типов: {e}")
            return False
    
    def diagnose_autogenerate_issues(self):
        """Диагностирует проблемы с автогенерацией"""
        print("\n🤖 Диагностика автогенерации Alembic:")
        print("-" * 50)
        
        try:
            # Проверяем переменные окружения
            database_url = os.getenv('DATABASE_URL', settings.DATABASE_URL)
            print(f"✅ DATABASE_URL: {database_url[:50]}...")
            
            # Проверяем что можем подключиться
            print("🔍 Проверка подключения к БД...")
            
            # Временно создаем engine для проверки
            from sqlalchemy import create_engine
            engine = create_engine(database_url.replace('+asyncpg', '+psycopg2'))
            
            with engine.connect() as conn:
                print("✅ Подключение к БД успешно")
                
                # Проверяем версию PostgreSQL
                version = conn.execute(sa.text("SELECT version()")).fetchone()[0]
                print(f"📊 PostgreSQL: {version.split(',')[0]}")
            
            engine.dispose()
            
            # Проверяем кэширование метаданных
            print("\n🧹 Проверка кэширования:")
            
            # Очистка кэша модулей
            modules_to_clear = [name for name in sys.modules.keys() 
                              if name.startswith('app.database')]
            print(f"🔄 Модули для очистки: {len(modules_to_clear)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка диагностики автогенерации: {e}")
            import traceback
            traceback.print_exc()
            return False

class MigrationSyncChecker:
    """Класс для проверки синхронизации миграций"""
    
    def __init__(self):
        self.db_connection = None
        self.diagnostics = AlembicDiagnostics()
        
    async def connect_db(self):
        """Подключение к базе данных"""
        self.db_connection = await asyncpg.connect(
            settings.DATABASE_URL.replace('+asyncpg', '')
        )
    
    async def disconnect_db(self):
        """Отключение от базы данных"""
        if self.db_connection:
            await self.db_connection.close()
    
    async def get_db_tables(self) -> List[str]:
        """Получает список таблиц из БД"""
        tables = await self.db_connection.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        return [t['table_name'] for t in tables]
    
    def get_model_tables(self) -> List[str]:
        """Получает список таблиц из моделей SQLAlchemy"""
        return list(Base.metadata.tables.keys())
    
    async def get_db_columns(self, table_name: str) -> Dict:
        """Получает информацию о колонках таблицы из БД"""
        columns = await self.db_connection.fetch("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        
        return {col['column_name']: col for col in columns}
    
    def get_model_columns(self, table_name: str) -> Dict:
        """Получает информацию о колонках таблицы из моделей"""
        if table_name not in Base.metadata.tables:
            return {}
            
        table = Base.metadata.tables[table_name]
        columns = {}
        
        for column in table.columns:
            columns[column.name] = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'default': str(column.default) if column.default else None,
                'primary_key': column.primary_key
            }
        
        return columns
    
    async def check_table_sync(self, table_name: str):
        """Проверяет синхронизацию конкретной таблицы"""
        print(f"\n📋 Таблица: {table_name}")
        print("-" * 50)
        
        # Получаем данные
        db_columns = await self.get_db_columns(table_name)
        model_columns = self.get_model_columns(table_name)
        
        db_column_names = set(db_columns.keys())
        model_column_names = set(model_columns.keys())
        
        # Проверяем различия
        missing_in_db = model_column_names - db_column_names
        missing_in_model = db_column_names - model_column_names
        common_columns = db_column_names & model_column_names
        
        # Результаты
        if missing_in_db:
            print(f"❌ Отсутствуют в БД ({len(missing_in_db)}): {', '.join(sorted(missing_in_db))}")
        
        if missing_in_model:
            print(f"⚠️  Есть в БД, но нет в модели ({len(missing_in_model)}): {', '.join(sorted(missing_in_model))}")
        
        if common_columns:
            print(f"✅ Общие поля ({len(common_columns)}): {', '.join(sorted(common_columns))}")
        
        # Детальная проверка общих полей
        type_mismatches = []
        for col_name in common_columns:
            db_col = db_columns[col_name]
            model_col = model_columns[col_name]
            
            # Упрощенная проверка типов (PostgreSQL vs SQLAlchemy имеют разные названия)
            if self._types_mismatch(db_col['data_type'], model_col['type']):
                type_mismatches.append(f"{col_name}: DB={db_col['data_type']} vs Model={model_col['type']}")
        
        if type_mismatches:
            print(f"⚠️  Несовпадения типов ({len(type_mismatches)}):")
            for mismatch in type_mismatches:
                print(f"   - {mismatch}")
        
        return {
            'missing_in_db': missing_in_db,
            'missing_in_model': missing_in_model,
            'type_mismatches': type_mismatches
        }
    
    def _types_mismatch(self, db_type: str, model_type: str) -> bool:
        """Упрощенная проверка соответствия типов"""
        # Базовые соответствия типов
        type_mapping = {
            'character varying': ['VARCHAR', 'String'],
            'uuid': ['UUID', 'PGUUID'],
            'integer': ['INTEGER', 'Integer'],
            'boolean': ['BOOLEAN', 'Boolean'],
            'timestamp with time zone': ['TIMESTAMP', 'DateTime'],
            'json': ['JSON'],
            'text': ['TEXT', 'Text'],
            'double precision': ['FLOAT', 'Float'],
            'USER-DEFINED': ['Enum']  # Для enum типов
        }
        
        for db_base, model_bases in type_mapping.items():
            if db_type.lower().startswith(db_base.lower()):
                return not any(mb in model_type for mb in model_bases)
        
        return False
    
    async def check_alembic_status(self):
        """Проверяет статус Alembic"""
        print("\n🔧 Статус Alembic:")
        print("-" * 30)
        
        try:
            # Проверяем таблицу alembic_version
            version = await self.db_connection.fetchval(
                'SELECT version_num FROM alembic_version'
            )
            print(f"✅ Текущая версия: {version}")
            
            # Проверяем файлы миграций
            migrations_dir = project_root / "alembic" / "versions"
            migration_files = list(migrations_dir.glob("*.py"))
            print(f"📁 Файлов миграций: {len(migration_files)}")
            
            if migration_files:
                latest_file = max(migration_files, key=lambda x: x.name)
                print(f"📄 Последний файл: {latest_file.name}")
                
                # Проверяем содержимое последней миграции
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if 'def upgrade() -> None:\n    pass' in content:
                        print("⚠️  Последняя миграция ПУСТАЯ!")
                    else:
                        print("✅ Последняя миграция содержит изменения")
                        
                except Exception as e:
                    print(f"❌ Ошибка чтения миграции: {e}")
            
        except Exception as e:
            print(f"❌ Ошибка проверки Alembic: {e}")
    
    async def run_full_check(self):
        """Выполняет полную проверку синхронизации"""
        print("="*60)
        print("🔍 ПРОВЕРКА СИНХРОНИЗАЦИИ МИГРАЦИЙ")
        print("="*60)
        
        # Запускаем диагностику Alembic
        print("\n🔧 ДИАГНОСТИКА ALEMBIC")
        print("="*60)
        
        config_ok = self.diagnostics.check_alembic_configuration()
        metadata_ok = self.diagnostics.check_sqlalchemy_metadata()
        imports_ok = self.diagnostics.check_alembic_imports()
        enums_ok = self.diagnostics.check_enum_registration()
        autogen_ok = self.diagnostics.diagnose_autogenerate_issues()
        
        diagnostics_score = sum([config_ok, metadata_ok, imports_ok, enums_ok, autogen_ok])
        print(f"\n📊 Результат диагностики: {diagnostics_score}/5 компонентов работают")
        
        await self.connect_db()
        
        try:
            # Проверяем статус Alembic
            await self.check_alembic_status()
            
            # Получаем списки таблиц
            db_tables = await self.get_db_tables()
            model_tables = self.get_model_tables()
            
            print(f"\n📊 Общая статистика:")
            print(f"   Таблиц в БД: {len(db_tables)}")
            print(f"   Таблиц в моделях: {len(model_tables)}")
            
            # Находим общие таблицы
            common_tables = set(db_tables) & set(model_tables)
            missing_in_db = set(model_tables) - set(db_tables)
            extra_in_db = set(db_tables) - set(model_tables)
            
            if missing_in_db:
                print(f"❌ Таблицы отсутствуют в БД: {', '.join(missing_in_db)}")
            
            if extra_in_db:
                print(f"⚠️  Лишние таблицы в БД: {', '.join(extra_in_db)}")
            
            # Проверяем синхронизацию каждой таблицы
            print("\n" + "="*60)
            print("ДЕТАЛЬНАЯ ПРОВЕРКА ТАБЛИЦ")
            print("="*60)
            
            total_issues = 0
            critical_issues = 0
            
            for table_name in sorted(common_tables):
                result = await self.check_table_sync(table_name)
                issues = len(result['missing_in_db']) + len(result['missing_in_model']) + len(result['type_mismatches'])
                total_issues += issues
                
                # Критические проблемы - отсутствующие поля в БД
                if result['missing_in_db']:
                    critical_issues += len(result['missing_in_db'])
            
            # Итоговый результат
            print("\n" + "="*60)
            print("РЕКОМЕНДАЦИИ")
            print("="*60)
            
            if total_issues == 0:
                print("🎉 ВСЕ ТАБЛИЦЫ СИНХРОНИЗИРОВАНЫ!")
            else:
                print(f"⚠️  НАЙДЕНО {total_issues} ПРОБЛЕМ СИНХРОНИЗАЦИИ")
                print(f"❌ Критических проблем: {critical_issues}")
                
                if critical_issues > 0:
                    print("\n🔧 ДЕЙСТВИЯ:")
                    print("1. Запустите: python scripts/reset_migrations.py")
                    print("2. Если проблема повторится, проверьте импорты в alembic/env.py")
                    print("3. Очистите кэш Python: rm -rf __pycache__ app/__pycache__")
                    
                if diagnostics_score < 5:
                    print("4. Исправьте проблемы с конфигурацией Alembic (см. диагностику выше)")
                    
            print("="*60)
            
        finally:
            await self.disconnect_db()

async def main():
    """Главная функция"""
    checker = MigrationSyncChecker()
    await checker.run_full_check()

if __name__ == "__main__":
    asyncio.run(main()) 