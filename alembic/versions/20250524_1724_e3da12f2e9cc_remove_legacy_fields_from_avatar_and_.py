"""Remove legacy fields from Avatar and AvatarPhoto models

⚠️  ВАЖНО: Эта миграция удаляет Legacy поля. Убедитесь что:
1. Все данные migrated
2. Код не использует Legacy поля  
3. Создан бэкап БД

Legacy поля к удалению:
- avatars.is_draft → заменено на status
- avatars.photo_key → не используется 
- avatars.preview_key → не используется
- avatar_photos.order → заменено на upload_order

Revision ID: e3da12f2e9cc
Revises: b2df0db38780
Create Date: 2025-05-24 17:24:50.218810+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3da12f2e9cc'
down_revision: Union[str, None] = 'b2df0db38780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Удаляем Legacy поля из моделей
    
    ⚠️ КРИТИЧНО: Убедитесь что все данные перенесены и код обновлён!
    """
    
    # 🔽 Удаляем Legacy поля из таблицы avatars
    print("🗑️  Удаляем Legacy поля из таблицы avatars...")
    
    # Удаляем is_draft (заменено на status)
    try:
        op.drop_column('avatars', 'is_draft')
        print("✅ Удалено поле avatars.is_draft")
    except Exception as e:
        print(f"⚠️  Поле avatars.is_draft не найдено или уже удалено: {e}")
    
    # Удаляем photo_key (не используется)
    try:
        op.drop_column('avatars', 'photo_key')
        print("✅ Удалено поле avatars.photo_key")
    except Exception as e:
        print(f"⚠️  Поле avatars.photo_key не найдено или уже удалено: {e}")
    
    # Удаляем preview_key (не используется)
    try:
        op.drop_column('avatars', 'preview_key')
        print("✅ Удалено поле avatars.preview_key")
    except Exception as e:
        print(f"⚠️  Поле avatars.preview_key не найдено или уже удалено: {e}")
    
    # 🔽 Удаляем Legacy поля из таблицы avatar_photos
    print("🗑️  Удаляем Legacy поля из таблицы avatar_photos...")
    
    # Удаляем order (заменено на upload_order)
    try:
        op.drop_column('avatar_photos', 'order')
        print("✅ Удалено поле avatar_photos.order")
    except Exception as e:
        print(f"⚠️  Поле avatar_photos.order не найдено или уже удалено: {e}")
    
    print("🎯 Миграция Legacy полей завершена!")


def downgrade() -> None:
    """
    Восстанавливаем Legacy поля (для отката)
    
    ⚠️ ВНИМАНИЕ: Данные в Legacy полях будут потеряны при откате!
    """
    
    print("🔄 Восстанавливаем Legacy поля...")
    
    # 🔽 Восстанавливаем поля в таблице avatars
    op.add_column('avatars', sa.Column('is_draft', sa.Boolean, default=True, nullable=True))
    op.add_column('avatars', sa.Column('photo_key', sa.String(255), nullable=True))
    op.add_column('avatars', sa.Column('preview_key', sa.String(255), nullable=True))
    
    # 🔽 Восстанавливаем поля в таблице avatar_photos  
    op.add_column('avatar_photos', sa.Column('order', sa.Integer, default=0, nullable=True))
    
    print("⚠️  Legacy поля восстановлены, но данные потеряны!")
    print("🔄 Рекомендуется восстановить из бэкапа")
