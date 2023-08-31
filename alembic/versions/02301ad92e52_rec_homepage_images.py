"""rec_homepage_images

Revision ID: 02301ad92e52
Revises: 74833829634e
Create Date: 2023-08-30 23:39:23.874598

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02301ad92e52'
down_revision = '74833829634e'
branch_labels = None
depends_on = None


def upgrade():
    # Add `topic_image` column to `movie_recommendations`
    op.add_column(
        'movie_recommendations',
        sa.Column('topic_image', sa.String(length=256), nullable=True, server_default='')
    )


def downgrade():
    # Remove `topic_image` column from `movie_recommendations`
    op.drop_column('movie_recommendations', 'topic_image')
