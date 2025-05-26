"""Rename hashed_password column to password in users table

Revision ID: rename_password_column
Revises: fbd9d685eaa6
Create Date: 2025-05-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'rename_password_column'
down_revision = 'fbd9d685eaa6'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('users', 'hashed_password', new_column_name='password')

def downgrade():
    op.alter_column('users', 'password', new_column_name='hashed_password')
