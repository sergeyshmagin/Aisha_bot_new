"""remove_other_gender_from_avatar_enum

Revision ID: 6f8aaa37f3fa
Revises: 5088361401fe
Create Date: 2025-05-24 00:17:34.993907+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa# revision identifiers, used by Alembic.
revision: str = '6f8aaa37f3fa'
down_revision: Union[str, None] = '5088361401fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = Nonedef upgrade() -> None:
    # Удаляем значение 'other' из AvatarGender enum
    # Сначала обновляем все записи с 'other' на 'male' (если есть)
    op.execute("UPDATE avatars SET gender = 'male' WHERE gender = 'other'")
    
    # Создаем новый enum без 'other'
    op.execute("CREATE TYPE avatargender_new AS ENUM ('male', 'female')")
    
    # Изменяем столбец на новый enum
    op.execute("ALTER TABLE avatars ALTER COLUMN gender TYPE avatargender_new USING gender::text::avatargender_new")
    
    # Удаляем старый enum
    op.execute("DROP TYPE avatargender")
    
    # Переименовываем новый enum
    op.execute("ALTER TYPE avatargender_new RENAME TO avatargender")def downgrade() -> None:
    # Создаем старый enum с 'other'
    op.execute("CREATE TYPE avatargender_new AS ENUM ('male', 'female', 'other')")
    
    # Изменяем столбец на старый enum
    op.execute("ALTER TABLE avatars ALTER COLUMN gender TYPE avatargender_new USING gender::text::avatargender_new")
    
    # Удаляем новый enum
    op.execute("DROP TYPE avatargender")
    
    # Переименовываем обратно
    op.execute("ALTER TYPE avatargender_new RENAME TO avatargender")
