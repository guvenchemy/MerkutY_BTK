"""fix processed_transcripts uniqueness to be per-user

Revision ID: b7c9d1e2f3a4
Revises: a1b2c3d4e5f6
Create Date: 2025-08-07 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c9d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraint if exists
    op.execute("ALTER TABLE processed_transcripts DROP CONSTRAINT IF EXISTS processed_transcripts_video_id_key;")
    # Drop index (unique or non-unique) on video_id to redefine properly
    try:
        op.drop_index(op.f('ix_processed_transcripts_video_id'), table_name='processed_transcripts')
    except Exception:
        # ignore if index name differs or doesn't exist
        pass

    # Create non-unique index on video_id for lookup speed
    op.create_index(op.f('ix_processed_transcripts_video_id'), 'processed_transcripts', ['video_id'], unique=False)

    # Create composite unique constraint only if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = 'uq_transcript_video_user' 
                AND table_name = 'processed_transcripts'
                AND table_schema = 'public'
            ) THEN
                ALTER TABLE processed_transcripts 
                ADD CONSTRAINT uq_transcript_video_user 
                UNIQUE (video_id, added_by_user_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop composite unique constraint if exists
    op.execute("ALTER TABLE processed_transcripts DROP CONSTRAINT IF EXISTS uq_transcript_video_user;")
    # Recreate unique index on video_id (previous behavior) if desired
    try:
        op.drop_index(op.f('ix_processed_transcripts_video_id'), table_name='processed_transcripts')
    except Exception:
        pass
    op.create_index(op.f('ix_processed_transcripts_video_id'), 'processed_transcripts', ['video_id'], unique=True) 