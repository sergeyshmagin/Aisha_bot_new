"""
Скрипт для управления базой данных
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from aisha_v2.app.core.config import settings

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем путь к корню проекта
PROJECT_ROOT = Path(__file__).parent.parent


def get_alembic_config() -> Config:
    """Создать конфигурацию Alembic"""
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.ASYNC_DATABASE_URL)
    return config


async def check_database_connection():
    """Проверить подключение к базе данных"""
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    finally:
        await engine.dispose()


def upgrade_database(revision: str = "head"):
    """Обновить базу данных до указанной ревизии"""
    config = get_alembic_config()
    command.upgrade(config, revision)
    logger.info(f"Database upgraded to {revision}")


def downgrade_database(revision: str):
    """Откатить базу данных до указанной ревизии"""
    config = get_alembic_config()
    command.downgrade(config, revision)
    logger.info(f"Database downgraded to {revision}")


def create_migration(message: str):
    """Создать новую миграцию"""
    config = get_alembic_config()
    command.revision(config, message=message, autogenerate=True)
    logger.info(f"Created new migration with message: {message}")


def show_migrations():
    """Показать список миграций"""
    config = get_alembic_config()
    command.history(config)


async def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument("command", choices=["upgrade", "downgrade", "create", "show", "check"])
    parser.add_argument("--revision", help="Target revision for upgrade/downgrade")
    parser.add_argument("--message", help="Migration message")

    args = parser.parse_args()

    # Проверяем подключение к БД
    if not await check_database_connection():
        sys.exit(1)

    try:
        if args.command == "upgrade":
            upgrade_database(args.revision or "head")
        elif args.command == "downgrade":
            if not args.revision:
                logger.error("Revision is required for downgrade")
                sys.exit(1)
            downgrade_database(args.revision)
        elif args.command == "create":
            if not args.message:
                logger.error("Message is required for create")
                sys.exit(1)
            create_migration(args.message)
        elif args.command == "show":
            show_migrations()
        elif args.command == "check":
            logger.info("Database connection is OK")

    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
