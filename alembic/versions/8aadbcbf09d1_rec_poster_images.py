"""rec_poster_images

Revision ID: 8aadbcbf09d1
Revises: 02301ad92e52
Create Date: 2023-09-24 22:54:32.506057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8aadbcbf09d1'
down_revision = '02301ad92e52'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('movie_recommendations', sa.Column('poster_1',
                                                     sa.String(length=256),
                                                     nullable=True))
    op.add_column('movie_recommendations', sa.Column('poster_2',
                                                     sa.String(length=256),
                                                     nullable=True))
    op.add_column('movie_recommendations', sa.Column('poster_3',
                                                     sa.String(length=256),
                                                     nullable=True))


def downgrade():
    op.drop_column('movie_recommendations', 'poster_1')
    op.drop_column('movie_recommendations', 'poster_2')
    op.drop_column('movie_recommendations', 'poster_3')
