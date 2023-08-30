"""support_genre_types_in_db

Revision ID: 74833829634e
Revises: 5fa0bde75611
Create Date: 2023-08-21 19:51:55.178126

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '74833829634e'
down_revision = '5fa0bde75611'
branch_labels = None
depends_on = None


def upgrade():
    # create the 'genre' table
    op.create_table(
        'genre',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(64), unique=True, nullable=False)
    )

    # create the 'movie_genre' table
    op.create_table(
        'movie_genre',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('movie_uuid', sa.CHAR(36), sa.ForeignKey('movie_data.uuid'), nullable=False), # noqa
        sa.Column('genre_id', sa.Integer, sa.ForeignKey('genre.id'), nullable=False), # noqa
        sa.UniqueConstraint('movie_uuid', 'genre_id', name='unique_movie_genre') # noqa
    )

    # add new columns to 'movie_recommendations' table
    op.add_column('movie_recommendations', sa.Column('genre_1', sa.Integer, sa.ForeignKey('genre.id'), nullable=True)) # noqa
    op.add_column('movie_recommendations', sa.Column('genre_2', sa.Integer, sa.ForeignKey('genre.id'), nullable=True)) # noqa
    op.add_column('movie_recommendations', sa.Column('genre_3', sa.Integer, sa.ForeignKey('genre.id'), nullable=True)) # noqa


def downgrade():
    # 1. Drop the foreign key constraints
    op.drop_constraint('movie_recommendations_ibfk_1', 'movie_recommendations', type_='foreignkey') # noqa
    op.drop_constraint('movie_recommendations_ibfk_2', 'movie_recommendations', type_='foreignkey') # noqa
    op.drop_constraint('movie_recommendations_ibfk_3', 'movie_recommendations', type_='foreignkey') # noqa

    # 2. Remove the columns
    op.drop_column('movie_recommendations', 'genre_3')
    op.drop_column('movie_recommendations', 'genre_2')
    op.drop_column('movie_recommendations', 'genre_1')

    # Remove the 'movie_genre' and 'genre' tables
    op.drop_table('movie_genre')
    op.drop_table('genre')
