"""add upload_batch_id to synthetic_data

Revision ID: e78337f03b8b
Revises: 
Create Date: 2026-03-26 16:02:33.581146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e78337f03b8b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add upload_batch_id column to synthetic_data table
    op.add_column('synthetic_data', sa.Column('upload_batch_id', sa.String(64), nullable=True))
    # Create index for upload_batch_id
    op.create_index('ix_synthetic_data_upload_batch_id', 'synthetic_data', ['upload_batch_id'])


def downgrade() -> None:
    # Drop index first, then column
    op.drop_index('ix_synthetic_data_upload_batch_id', table_name='synthetic_data')
    op.drop_column('synthetic_data', 'upload_batch_id')
