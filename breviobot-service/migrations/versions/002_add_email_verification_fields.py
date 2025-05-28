"""Add is_verified and verification_token columns to users table

Revision ID: 002_add_email_verification_fields
Revises: 001_rename_password_column
Create Date: 2025-05-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_email_verification_fields'
down_revision = '001_rename_password_column'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('users', sa.Column('verification_token', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')
