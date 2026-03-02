"""compatibility bridge for historical simulation revision

Revision ID: 20260210_complete_simulation
Revises: 20260127_sensitive_hash
Create Date: 2026-02-10

This migration is intentionally a no-op. Some local databases were stamped
with this historical revision id, but the file was missing in repository
history, which breaks `alembic upgrade` with "Can't locate revision".
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '20260210_complete_simulation'
down_revision: Union[str, None] = '20260127_sensitive_hash'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op compatibility revision."""


def downgrade() -> None:
    """No-op compatibility revision."""

