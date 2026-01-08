"""add_email_fields_to_user_and_alert

Revision ID: e8423f935861
Revises: e9850316121c
Create Date: 2026-01-08 12:51:15.056736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e8423f935861'
down_revision: Union[str, Sequence[str], None] = 'e9850316121c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add email fields to users and alerts tables."""
    # Add email preference fields to users table
    op.add_column('users', sa.Column('email_alerts_enabled', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('users', sa.Column('email_digest_enabled', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('users', sa.Column('trial_reminder_sent', sa.Boolean(), nullable=True, server_default='false'))

    # Add email tracking fields to alerts table
    op.add_column('alerts', sa.Column('user_id', sa.String(), nullable=True))
    op.add_column('alerts', sa.Column('email_sent', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('alerts', sa.Column('email_sent_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)
    op.create_foreign_key('fk_alerts_user_id', 'alerts', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema - remove email fields."""
    # Remove from alerts table
    op.drop_constraint('fk_alerts_user_id', 'alerts', type_='foreignkey')
    op.drop_index(op.f('ix_alerts_user_id'), table_name='alerts')
    op.drop_column('alerts', 'email_sent_at')
    op.drop_column('alerts', 'email_sent')
    op.drop_column('alerts', 'user_id')

    # Remove from users table
    op.drop_column('users', 'trial_reminder_sent')
    op.drop_column('users', 'email_digest_enabled')
    op.drop_column('users', 'email_alerts_enabled')
