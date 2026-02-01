"""add price predictions table

Revision ID: add_price_predictions
Revises: 
Create Date: 2026-02-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_price_predictions'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create price_predictions table."""
    op.create_table(
        'price_predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('prediction', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('sentiment_summary', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('key_factors', sa.Text(), nullable=False),
        sa.Column('news_analyzed', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_symbol_created_at', 'price_predictions', ['symbol', 'created_at'], unique=False)
    op.create_index(op.f('ix_price_predictions_symbol'), 'price_predictions', ['symbol'], unique=False)


def downgrade() -> None:
    """Drop price_predictions table."""
    op.drop_index(op.f('ix_price_predictions_symbol'), table_name='price_predictions')
    op.drop_index('idx_symbol_created_at', table_name='price_predictions')
    op.drop_table('price_predictions')
