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
    # word_count
    op.add_column('url_content', sa.Column('word_count', sa.Integer(), server_default='0', nullable=False))
    # added_by_user_id
    op.add_column('url_content', sa.Column('added_by_user_id', sa.Integer(), nullable=True))

    # Create FK to users
    op.create_foreign_key(
        'fk_url_content_user', 'url_content', 'users', ['added_by_user_id'], ['id'], ondelete='SET NULL'
    )

    # Create composite unique constraint
    op.create_unique_constraint('uq_urlcontent_url_user', 'url_content', ['url', 'added_by_user_id'])


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