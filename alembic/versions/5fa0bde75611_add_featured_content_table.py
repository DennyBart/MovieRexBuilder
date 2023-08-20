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

# Define ContentType enum for MySQL
content_types = ('recently_added', 'director', 'actor',
                 'genre', 'featured_movie')
ContentType = sa.Enum(*content_types, name='contenttype')


def upgrade():
    # Create ContentType ENUM type
    ContentType.create(op.get_bind(), checkfirst=False)

    # Create featured_content table
    op.create_table(
        'featured_content',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('content_type', ContentType, nullable=False),
        sa.Column('group_title', sa.String(256), nullable=True),
        sa.Column('recommendation_uuid', sa.CHAR(36),
                  sa.ForeignKey('movie_recommendations.uuid'),
                  nullable=False),
        sa.Column('replaced_at', sa.DateTime, nullable=True),
        sa.Column('live_list', sa.Boolean, nullable=False)
    )

    op.add_column('cast_name',
                  sa.Column('vip', sa.Boolean, nullable=False,
                            default=False, server_default=sa.text('0')))

    op.add_column('movie_recommendations',
                  sa.Column('genre', sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column('movie_recommendations', 'genre')
    op.drop_column('cast_name', 'vip')
    op.drop_table('featured_content')
    ContentType.drop(op.get_bind(), checkfirst=False)
