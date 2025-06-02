"""Final remove order field from avatar_photos

Revision ID: final_remove_order
Revises: e3e0f1fd5585  
Create Date: 2025-05-24 22:20:00.000000+05:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'final_remove_order'
down_revision: Union[str, None] = 'e3e0f1fd5585'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Удаляем поле order окончательно"""
    print("🗑️  Удаляем legacy поле order из avatar_photos...")
    
    try:
        op.drop_column('avatar_photos', 'order')
        print("✅ Удалено поле avatar_photos.order")
    except Exception as e:
        print(f"⚠️  Поле avatar_photos.order не найдено или уже удалено: {e}")
    
    print("🎯 Финальное удаление поля order завершено!")

def downgrade() -> None:
    """Восстанавливаем поле order"""
    print("🔄 Восстанавливаем поле order...")
    op.add_column('avatar_photos', sa.Column('order', sa.Integer, default=0, nullable=True))
    print("⚠️  Поле order восстановлено!")
