"""Add cross_platform_matches table

Revision ID: 7353256d44b8
Revises: a2b3c4d5e6f7
Create Date: 2026-01-05 02:45:22.137590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7353256d44b8'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cross_platform_matches table
    op.create_table('cross_platform_matches',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.String(length=255), nullable=False),
    sa.Column('topic', sa.String(length=500), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('kalshi_market_id', sa.String(length=255), nullable=True),
    sa.Column('kalshi_title', sa.Text(), nullable=True),
    sa.Column('kalshi_yes_price', sa.Float(), nullable=True),
    sa.Column('kalshi_volume', sa.Float(), nullable=True),
    sa.Column('kalshi_close_time', sa.DateTime(), nullable=True),
    sa.Column('polymarket_market_id', sa.String(length=255), nullable=True),
    sa.Column('polymarket_title', sa.Text(), nullable=True),
    sa.Column('polymarket_yes_price', sa.Float(), nullable=True),
    sa.Column('polymarket_volume', sa.Float(), nullable=True),
    sa.Column('polymarket_close_time', sa.DateTime(), nullable=True),
    sa.Column('price_gap_cents', sa.Float(), nullable=True),
    sa.Column('gap_direction', sa.String(length=20), nullable=True),
    sa.Column('combined_volume', sa.Float(), nullable=True),
    sa.Column('similarity_score', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('ai_analysis', sa.Text(), nullable=True),
    sa.Column('news_headlines', sa.JSON(), nullable=True),
    sa.Column('gap_explanation', sa.Text(), nullable=True),
    sa.Column('momentum_summary', sa.Text(), nullable=True),
    sa.Column('key_risks', sa.Text(), nullable=True),
    sa.Column('discovered_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('ai_generated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['kalshi_market_id'], ['markets.id'], ),
    sa.ForeignKeyConstraint(['polymarket_market_id'], ['markets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cross_platform_matches_category'), 'cross_platform_matches', ['category'], unique=False)
    op.create_index(op.f('ix_cross_platform_matches_is_active'), 'cross_platform_matches', ['is_active'], unique=False)
    op.create_index(op.f('ix_cross_platform_matches_kalshi_market_id'), 'cross_platform_matches', ['kalshi_market_id'], unique=False)
    op.create_index(op.f('ix_cross_platform_matches_match_id'), 'cross_platform_matches', ['match_id'], unique=True)
    op.create_index(op.f('ix_cross_platform_matches_polymarket_market_id'), 'cross_platform_matches', ['polymarket_market_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_cross_platform_matches_polymarket_market_id'), table_name='cross_platform_matches')
    op.drop_index(op.f('ix_cross_platform_matches_match_id'), table_name='cross_platform_matches')
    op.drop_index(op.f('ix_cross_platform_matches_kalshi_market_id'), table_name='cross_platform_matches')
    op.drop_index(op.f('ix_cross_platform_matches_is_active'), table_name='cross_platform_matches')
    op.drop_index(op.f('ix_cross_platform_matches_category'), table_name='cross_platform_matches')
    op.drop_table('cross_platform_matches')
