#!/usr/bin/env python3
"""
Скрипт для диагностики и исправления проблем с alembic/env.py

Проверяет:
- Корректность импортов
- Настройки target_metadata
- Конфигурацию подключения к БД
- Правильность инициализации
"""
import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AlembicEnvDiagnoser:
    """Класс для диагностики и исправления alembic/env.py"""
    
    def __init__(self):
        self.project_root = project_root
        self.alembic_dir = self.project_root / "alembic"
        self.env_py = self.alembic_dir / "env.py"
        
    def check_env_py_exists(self):
        """Проверяет существование alembic/env.py"""
        print("🔍 Проверка существования alembic/env.py...")
        
        if self.env_py.exists():
            print("   ✅ Файл alembic/env.py найден")
            return True
        else:
            print("   ❌ Файл alembic/env.py не найден")
            return False
    
    def read_env_py(self):
        """Читает содержимое env.py"""
        try:
            with open(self.env_py, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"   ❌ Ошибка чтения env.py: {e}")
            return None
    
    def check_imports(self, content):
        """Проверяет импорты в env.py"""
        print("\n🔄 Проверка импортов в env.py...")
        
        required_imports = [
            ('from app.database.models import Base', 'Импорт Base'),
            ('from app.core.config import settings', 'Импорт settings'),
            ('target_metadata = Base.metadata', 'Настройка target_metadata'),
        ]
        
        issues = []
        
        for import_line, description in required_imports:
            if import_line in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
                issues.append(import_line)
        
        return issues
    
    def check_database_url_config(self, content):
        """Проверяет конфигурацию DATABASE_URL"""
        print("\n🔗 Проверка конфигурации DATABASE_URL...")
        
        if 'settings.DATABASE_URL' in content:
            print("   ✅ Используется settings.DATABASE_URL")
            return True
        elif 'config.get_main_option("sqlalchemy.url")' in content:
            print("   ⚠️  Используется конфигурация из alembic.ini")
            return False
        else:
            print("   ❌ DATABASE_URL не настроен")
            return False
    
    def create_fixed_env_py(self):
        """Создает исправленную версию env.py"""
        print("\n🔧 Создание исправленной версии env.py...")
        
        fixed_env_content = '''from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Добавляем корневую папку проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.database.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """Получает URL для подключения к базе данных"""
    # Используем DATABASE_URL из настроек
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Создаем конфигурацию для engine
    configuration = {
        'sqlalchemy.url': get_url(),
        'sqlalchemy.poolclass': pool.NullPool,
    }

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        try:
            # Создаем резервную копию
            backup_file = self.env_py.with_suffix('.py.backup')
            if self.env_py.exists():
                self.env_py.replace(backup_file)
                print(f"   💾 Создана резервная копия: {backup_file.name}")
            
            # Записываем исправленную версию
            with open(self.env_py, 'w', encoding='utf-8') as f:
                f.write(fixed_env_content)
            
            print("   ✅ Создана исправленная версия env.py")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка создания env.py: {e}")
            return False
    
    def test_env_py_import(self):
        """Тестирует что env.py может корректно импортировать модели"""
        print("\n🧪 Тестирование импорта в env.py...")
        
        try:
            # Симулируем импорт как в env.py
            old_path = sys.path.copy()
            
            # Добавляем путь как в env.py
            env_dir = self.alembic_dir
            sys.path.insert(0, str(env_dir.parent))
            
            # Тестируем импорты
            from app.core.config import settings as test_settings
            print("   ✅ app.core.config импортирован")
            
            from app.database.models import Base as test_base
            print("   ✅ app.database.models.Base импортирован")
            
            # Проверяем метаданные
            metadata = test_base.metadata
            tables = list(metadata.tables.keys())
            print(f"   ✅ Метаданные: {len(tables)} таблиц")
            
            # Проверяем avatars таблицу
            if 'avatars' in metadata.tables:
                avatars_table = metadata.tables['avatars']
                columns = [col.name for col in avatars_table.columns]
                
                fal_fields = ['training_type', 'fal_request_id']
                found_fal = [f for f in fal_fields if f in columns]
                
                print(f"   🎯 FAL AI поля в метаданных: {found_fal}")
                
                if found_fal:
                    print("   ✅ Модели корректно загружены с FAL AI полями")
                    success = True
                else:
                    print("   ⚠️  Модели загружены, но FAL AI поля отсутствуют")
                    success = False
            else:
                print("   ❌ Таблица avatars не найдена")
                success = False
            
            sys.path = old_path
            return success
            
        except Exception as e:
            sys.path = old_path
            print(f"   ❌ Ошибка тестирования импорта: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_alembic_ini(self):
        """Проверяет конфигурацию alembic.ini"""
        print("\n📋 Проверка alembic.ini...")
        
        alembic_ini = self.project_root / "alembic.ini"
        
        if not alembic_ini.exists():
            print("   ❌ alembic.ini не найден")
            return False
        
        try:
            with open(alembic_ini, 'r', encoding='utf-8') as f:
                ini_content = f.read()
            
            # Проверяем ключевые настройки
            checks = [
                ('script_location = alembic', 'Расположение скриптов'),
                ('file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s', 'Шаблон файлов'),
                ('sqlalchemy.url = postgresql', 'URL базы данных'),
            ]
            
            for check_line, description in checks:
                if check_line in ini_content:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ⚠️  {description} - возможно настроен по-другому")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка чтения alembic.ini: {e}")
            return False
    
    def run_full_diagnosis(self):
        """Выполняет полную диагностику"""
        print("="*60)
        print("🔧 ДИАГНОСТИКА ALEMBIC/ENV.PY")
        print("="*60)
        
        # Шаг 1: Проверяем существование файлов
        env_exists = self.check_env_py_exists()
        ini_ok = self.check_alembic_ini()
        
        if not env_exists:
            print("\n❌ env.py не найден, создаем новый...")
            self.create_fixed_env_py()
            env_exists = True
        
        # Шаг 2: Анализируем env.py
        if env_exists:
            content = self.read_env_py()
            if content:
                import_issues = self.check_imports(content)
                db_config_ok = self.check_database_url_config(content)
                
                # Если есть проблемы, предлагаем исправление
                if import_issues or not db_config_ok:
                    print(f"\n⚠️  Найдено {len(import_issues)} проблем с импортами")
                    print("🔧 Создаем исправленную версию...")
                    self.create_fixed_env_py()
        
        # Шаг 3: Тестируем импорт
        import_success = self.test_env_py_import()
        
        # Итоговая оценка
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТ ДИАГНОСТИКИ")
        print("="*60)
        
        score = sum([env_exists, ini_ok, import_success])
        total = 3
        
        print(f"Результат: {score}/{total} компонентов работают корректно")
        
        if score == total:
            print("🎉 Конфигурация Alembic в порядке!")
            print("✅ Можно запускать миграции")
        elif score >= 2:
            print("⚠️  Конфигурация работоспособна, но есть предупреждения")
            print("🔧 Рекомендуется запустить reset_migrations.py")
        else:
            print("❌ Серьезные проблемы с конфигурацией Alembic")
            print("🚨 Требуется ручное исправление")
        
        print("="*60)
        
        return score >= 2

def main():
    """Главная функция"""
    diagnoser = AlembicEnvDiagnoser()
    diagnoser.run_full_diagnosis()

if __name__ == "__main__":
    main() 