"""add_api_token_support

Revision ID: bed1480587a8
Revises: 46f91d773a88
Create Date: 2023-08-18 00:04:13.632140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bed1480587a8'
down_revision = '46f91d773a88'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'api_key',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('hashed_key', sa.String(64), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()), # noqa 
        sa.Column('expires_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP + INTERVAL 30 DAY')) # noqa
    )


def downgrade():
    op.drop_table('api_key')
