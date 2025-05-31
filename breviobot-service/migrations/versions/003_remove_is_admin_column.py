"""Remove is_admin column from users table

Revision ID: 003_remove_is_admin_column
Revises: 002_add_email_verification_fields
Create Date: 2025-05-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_remove_is_admin_column'
down_revision = '002_add_email_verification_fields'
branch_labels = None
depends_on = None

def upgrade():
    op.drop_column('users', 'is_admin')

def downgrade():
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false()))
