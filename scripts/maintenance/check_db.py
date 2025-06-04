"""
Скрипт для проверки структуры базы данных
"""
import asyncio
import asyncpg

async def check_db():
    # Подключаемся к базе данных
    conn = await asyncpg.connect('postgresql://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha')
    
    # Получаем список таблиц
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print('Таблицы в базе данных:')
    for table in tables:
        print(f"- {table['table_name']}")
    
    # Получаем структуру таблицы users
    columns = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'")
    print('\nКолонки в таблице users:')
    for col in columns:
        print(f"- {col['column_name']}: {col['data_type']}")
    
    # Проверяем наличие колонки timezone
    has_timezone = await conn.fetchval("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'timezone'")
    print(f"\nКолонка timezone {'существует' if has_timezone > 0 else 'не существует'} в таблице users")
    
    # Закрываем соединение
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_db())
