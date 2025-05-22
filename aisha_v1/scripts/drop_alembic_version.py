from sqlalchemy import create_engine, text

engine = create_engine('postgresql://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha_test')
with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version;'))
    conn.commit()
print('Таблица alembic_version удалена.') 