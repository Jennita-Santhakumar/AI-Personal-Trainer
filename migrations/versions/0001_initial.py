"""Initial schema — tables are created by SQLAlchemy init_db() on first startup.

Revision ID: 0001
Revises: 
Create Date: 2026-04-01

NOTE: Table creation is handled by `database.init_db()` (SQLAlchemy metadata.create_all).
This migration is a no-op baseline so `alembic upgrade head` succeeds.
Future schema changes should be added as new revisions here.
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are created by init_db() — nothing to do here.
    pass


def downgrade() -> None:
    pass
