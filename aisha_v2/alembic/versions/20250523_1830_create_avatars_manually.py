"""create avatars table manually

Revision ID: create_avatars_manually
Revises: eb97642710a3
Create Date: 2025-05-23 18:30:00.000000+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'create_avatars_manually'
down_revision: Union[str, None] = 'eb97642710a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем ENUM типы
    avatar_gender_enum = sa.Enum('male', 'female', 'other', name='avatargender')
    avatar_status_enum = sa.Enum('draft', 'uploading', 'ready', 'training', 'completed', 'error', 'cancelled', name='avatarstatus')
    avatar_type_enum = sa.Enum('character', 'style', 'custom', name='avatartype')
    photo_validation_status_enum = sa.Enum('pending', 'valid', 'invalid', 'duplicate', name='photovalidationstatus')
    
    avatar_gender_enum.create(op.get_bind())
    avatar_status_enum.create(op.get_bind())
    avatar_type_enum.create(op.get_bind())
    photo_validation_status_enum.create(op.get_bind())

    # Создаем таблицу avatars
    op.create_table('avatars',
        sa.Column('id', PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', PGUUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('gender', avatar_gender_enum, nullable=False),
        sa.Column('avatar_type', avatar_type_enum, nullable=False, default='character'),
        sa.Column('status', avatar_status_enum, nullable=False, default='draft'),
        sa.Column('finetune_id', sa.String(length=255), nullable=True),
        sa.Column('training_progress', sa.Integer(), nullable=False, default=0),
        sa.Column('training_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fal_mode', sa.String(length=20), nullable=False, default='character'),
        sa.Column('fal_iterations', sa.Integer(), nullable=False, default=500),
        sa.Column('fal_priority', sa.String(length=20), nullable=False, default='quality'),
        sa.Column('trigger_word', sa.String(length=50), nullable=False, default='TOK'),
        sa.Column('lora_rank', sa.Integer(), nullable=False, default=32),
        sa.Column('avatar_data', JSON(), nullable=False, default={}),
        sa.Column('training_config', JSON(), nullable=False, default={}),
        sa.Column('photos_count', sa.Integer(), nullable=False, default=0),
        sa.Column('generations_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_draft', sa.Boolean(), nullable=False, default=True),
        sa.Column('photo_key', sa.String(length=255), nullable=True),
        sa.Column('preview_key', sa.String(length=255), nullable=True),
    )
    
    # Создаем индексы
    op.create_index('ix_avatars_finetune_id', 'avatars', ['finetune_id'])
    op.create_index('ix_avatars_user_id', 'avatars', ['user_id'])

    # Создаем таблицу avatar_photos
    op.create_table('avatar_photos',
        sa.Column('id', PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('avatar_id', PGUUID(as_uuid=True), sa.ForeignKey('avatars.id'), nullable=False),
        sa.Column('user_id', PGUUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('minio_key', sa.String(length=255), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('upload_order', sa.Integer(), nullable=False),
        sa.Column('validation_status', photo_validation_status_enum, nullable=False, default='pending'),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(length=10), nullable=False),
        sa.Column('has_face', sa.Boolean(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('validation_error', sa.Text(), nullable=True),
        sa.Column('photo_metadata', JSON(), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False, default=0),
    )
    
    # Создаем индексы для avatar_photos
    op.create_index('ix_avatar_photos_file_hash', 'avatar_photos', ['file_hash'])


def downgrade() -> None:
    # Удаляем таблицы
    op.drop_table('avatar_photos')
    op.drop_table('avatars')
    
    # Удаляем ENUM типы
    avatar_gender_enum = sa.Enum('male', 'female', 'other', name='avatargender')
    avatar_status_enum = sa.Enum('draft', 'uploading', 'ready', 'training', 'completed', 'error', 'cancelled', name='avatarstatus')
    avatar_type_enum = sa.Enum('character', 'style', 'custom', name='avatartype')
    photo_validation_status_enum = sa.Enum('pending', 'valid', 'invalid', 'duplicate', name='photovalidationstatus')
    
    avatar_gender_enum.drop(op.get_bind())
    avatar_status_enum.drop(op.get_bind())
    avatar_type_enum.drop(op.get_bind())
    photo_validation_status_enum.drop(op.get_bind()) 