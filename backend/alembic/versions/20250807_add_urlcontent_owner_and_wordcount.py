"""add UrlContent owner and word_count; composite unique

Revision ID: a1b2c3d4e5f6
Revises: f78fdd85a51e
Create Date: 2025-08-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f78fdd85a51e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old unique on url if present (Postgres-specific)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'url_content_url_key'
            ) THEN
                ALTER TABLE url_content DROP CONSTRAINT url_content_url_key;
            END IF;
        END$$;
        """
    )

    # Add new columns if not exist
    # word_count - check if column exists first
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'url_content' AND column_name = 'word_count'
            ) THEN
                ALTER TABLE url_content ADD COLUMN word_count INTEGER DEFAULT 0 NOT NULL;
            END IF;
        END$$;
        """
    )
    
    # added_by_user_id - check if column exists first
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'url_content' AND column_name = 'added_by_user_id'
            ) THEN
                ALTER TABLE url_content ADD COLUMN added_by_user_id INTEGER;
            END IF;
        END$$;
        """
    )

    # Create FK to users if not exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_url_content_user'
            ) THEN
                ALTER TABLE url_content ADD CONSTRAINT fk_url_content_user 
                FOREIGN KEY (added_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
            END IF;
        END$$;
        """
    )

    # Create composite unique constraint if not exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_urlcontent_url_user'
            ) THEN
                ALTER TABLE url_content ADD CONSTRAINT uq_urlcontent_url_user 
                UNIQUE (url, added_by_user_id);
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    # Drop composite unique
    op.drop_constraint('uq_urlcontent_url_user', 'url_content', type_='unique')
    # Drop FK
    op.drop_constraint('fk_url_content_user', 'url_content', type_='foreignkey')
    # Drop columns
    op.drop_column('url_content', 'added_by_user_id')
    op.drop_column('url_content', 'word_count')
    # (Optionally) recreate unique on url
    op.create_unique_constraint('url_content_url_key', 'url_content', ['url']) 