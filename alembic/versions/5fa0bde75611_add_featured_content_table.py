"""add_featured_content_tble

Revision ID: 5fa0bde75611
Revises: bed1480587a8
Create Date: 2023-08-19 15:29:26.377790

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5fa0bde75611'
down_revision = 'bed1480587a8'
branch_labels = None
depends_on = None


def upgrade():
    # Create featured_content table
    op.create_table(
        'featured_content',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('content_type', sa.String(256), nullable=False),
        sa.Column('group_title', sa.String(256), nullable=True),
        sa.Column('recommendation_uuid', sa.CHAR(36),
                  sa.ForeignKey('movie_recommendations.uuid'),
                  nullable=False),
        sa.Column('replaced_at', sa.DateTime, nullable=True),
        sa.Column('live_list', sa.Boolean, nullable=False)
    )

    # Add an index to the replaced_at column
    op.create_index('index_replaced_at', 'featured_content', ['replaced_at'], unique=False) # noqa

    op.add_column('cast_name',
                  sa.Column('vip', sa.Boolean, nullable=False,
                            default=False, server_default=sa.text('0')))


def downgrade() -> None:
    op.drop_column('cast_name', 'vip')
    op.drop_table('featured_content')
