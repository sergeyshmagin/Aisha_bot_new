from sqlalchemy import create_engine, text

# Замените строку подключения на свою, если нужно
engine = create_engine('postgresql://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha_test')
with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE;'))
    conn.execute(text('CREATE SCHEMA public;'))
    conn.commit()
print('Схема public пересоздана, все таблицы удалены.') 