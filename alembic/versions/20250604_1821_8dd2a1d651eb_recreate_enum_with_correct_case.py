"""recreate_enum_with_correct_case

Revision ID: 8dd2a1d651eb
Revises: e518b8e01ac3
Create Date: 2025-06-04 18:21:41.513329+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dd2a1d651eb'
down_revision: Union[str, None] = 'e518b8e01ac3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Пересоздает enum типы с правильным регистром (lowercase)
    Удаляет старые enum и создает новые с правильными значениями
    """
    
    # ===== 1. ПЕРЕСОЗДАЕМ AVATARGENDER =====
    # Создаем временный тип
    op.execute("CREATE TYPE avatargender_temp AS ENUM ('male', 'female');")
    
    # Обновляем колонку с конвертацией
    op.execute("""
        ALTER TABLE avatars 
        ALTER COLUMN gender TYPE avatargender_temp 
        USING (LOWER(gender::text))::avatargender_temp;
    """)
    
    # Удаляем старый тип и переименовываем новый
    op.execute("DROP TYPE avatargender;")
    op.execute("ALTER TYPE avatargender_temp RENAME TO avatargender;")
    
    # ===== 2. ПЕРЕСОЗДАЕМ GENERATIONSTATUS =====
    # Создаем временный тип
    op.execute("""
        CREATE TYPE generationstatus_temp AS ENUM (
            'pending', 'processing', 'completed', 'failed', 'cancelled'
        );
    """)
    
    # Обновляем колонку с конвертацией
    op.execute("""
        ALTER TABLE image_generations 
        ALTER COLUMN status TYPE generationstatus_temp 
        USING (LOWER(status::text))::generationstatus_temp;
    """)
    
    # Удаляем старый тип и переименовываем новый
    op.execute("DROP TYPE generationstatus;")
    op.execute("ALTER TYPE generationstatus_temp RENAME TO generationstatus;")
    
    print("✅ Enum типы пересозданы с правильным регистром")


def downgrade() -> None:
    """
    Откатывает изменения обратно к uppercase enum
    """
    
    # ===== 1. ОТКАТ AVATARGENDER =====
    op.execute("CREATE TYPE avatargender_temp AS ENUM ('MALE', 'FEMALE');")
    
    op.execute("""
        ALTER TABLE avatars 
        ALTER COLUMN gender TYPE avatargender_temp 
        USING (UPPER(gender::text))::avatargender_temp;
    """)
    
    op.execute("DROP TYPE avatargender;")
    op.execute("ALTER TYPE avatargender_temp RENAME TO avatargender;")
    
    # ===== 2. ОТКАТ GENERATIONSTATUS =====
    op.execute("""
        CREATE TYPE generationstatus_temp AS ENUM (
            'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED'
        );
    """)
    
    op.execute("""
        ALTER TABLE image_generations 
        ALTER COLUMN status TYPE generationstatus_temp 
        USING (UPPER(status::text))::generationstatus_temp;
    """)
    
    op.execute("DROP TYPE generationstatus;")
    op.execute("ALTER TYPE generationstatus_temp RENAME TO generationstatus;")
    
    print("⬅️ Enum типы откачены к uppercase")
