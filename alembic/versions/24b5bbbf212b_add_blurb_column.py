"""Add blurb column

Revision ID: 24b5bbbf212b
Revises: 9c112b44c7fb
Create Date: 2023-06-19 22:44:16.014701

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24b5bbbf212b'
down_revision = '9c112b44c7fb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('movie_recommendations',
                  sa.Column('blurb', sa.Text))


def downgrade():
    op.drop_column('movie_recommendations', 'blurb')
