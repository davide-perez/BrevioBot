"""Add user_google_tokens table

Revision ID: 004_add_user_google_tokens_table
Revises: 003_remove_is_admin_column
Create Date: 2025-05-31 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_user_google_tokens_table'
down_revision = '003_remove_is_admin_column'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'user_google_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('token', sa.LargeBinary(), nullable=False)
    )

def downgrade():
    op.drop_table('user_google_tokens')
