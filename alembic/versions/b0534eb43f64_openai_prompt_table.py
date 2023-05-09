"""openai_prompt_table

Revision ID: b0534eb43f64
Revises: b9991574a199
Create Date: 2023-05-09 22:34:42.925783

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0534eb43f64'
down_revision = 'b9991574a199'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'openai_prompts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('prompt', sa.String(256), nullable=False),
        sa.Column('response', sa.String(256), nullable=False),
        sa.Column('searched_time', sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('openai_prompts')
