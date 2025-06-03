"""initial_schema_with_fal_ai_fields

Revision ID: 5088361401fe
Revises: 
Create Date: 2025-05-23 21:35:00.922235+05:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5088361401fe'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляем поля FAL AI в таблицу avatars"""
    
    # Создаем новые enum типы если их нет
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE avatartrainingtype AS ENUM ('portrait', 'style');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE falfinetunetype AS ENUM ('full', 'lora');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE falpriority AS ENUM ('speed', 'quality', 'high_res_only');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Добавляем новые поля в таблицу avatars если их нет
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_type avatartrainingtype DEFAULT 'portrait';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN fal_request_id VARCHAR(255);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN learning_rate FLOAT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN trigger_phrase VARCHAR(100);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN steps INTEGER;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN multiresolution_training BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN subject_crop BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN create_masks BOOLEAN DEFAULT false;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN captioning BOOLEAN DEFAULT true;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN finetune_type falfinetunetype DEFAULT 'lora';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN finetune_comment VARCHAR(255);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN diffusers_lora_file_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN config_file_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_logs TEXT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN training_error TEXT;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN webhook_url VARCHAR(500);
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN last_status_check TIMESTAMP WITH TIME ZONE;
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ADD COLUMN fal_response_data JSON DEFAULT '{}';
            EXCEPTION
                WHEN duplicate_column THEN null;
            END;
        END $$;
    """)
    
    # Обновляем существующее поле fal_priority на enum (если нужно)
    op.execute("""
        DO $$ BEGIN
            BEGIN
                ALTER TABLE avatars ALTER COLUMN fal_priority TYPE falpriority USING fal_priority::falpriority;
            EXCEPTION
                WHEN OTHERS THEN null;
            END;
        END $$;
    """)
    
    # Создаем индексы
    op.execute("""
        DO $$ BEGIN
            BEGIN
                CREATE INDEX ix_avatars_fal_request_id ON avatars (fal_request_id);
            EXCEPTION
                WHEN duplicate_table THEN null;
            END;
        END $$;
    """)



def downgrade() -> None:
    pass
