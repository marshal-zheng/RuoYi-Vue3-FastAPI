"""File assets hard cut-over: asset/binding tables, generator file field declarations, maintenance jobs.

Revision ID: 20261024_file_assets
Revises: 20261022_remark_v2
Create Date: 2026-10-24

No history is migrated (hard cut-over): `sys_user.avatar` is dropped and notice content is converted to
UTF-8 text in place; old `/profile/...` notice images are not rewritten. Take the documented database
backup first; the retired upload directory is left on disk.
"""

from alembic import op
from scripts.data_migrations import file_assets_v1

revision = '20261024_file_assets'
down_revision = '20261022_remark_v2'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        file_assets_v1.upgrade(op.get_bind())


def downgrade():
    # Assets created after the cut-over cannot be guessed back; restore from the cut-over backup instead.
    raise RuntimeError('file assets cut-over is not reversible by downgrade; use the documented restore path')
