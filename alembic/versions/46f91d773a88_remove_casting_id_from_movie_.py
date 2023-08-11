"""remove casting_id from movie_recommendations

Revision ID: 46f91d773a88
Revises: 1acad03f0b18
Create Date: 2023-08-11 17:34:31.046774

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '46f91d773a88'
down_revision = '1acad03f0b18'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('movie_recommendations', 'casting_id')


def downgrade() -> None:
    op.add_column('movie_recommendations', sa.Column('casting_id', sa.YOUR_DATA_TYPE, nullable=True))
