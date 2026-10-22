"""Exercise subtree batch writes through SQLAlchemy rather than mocked execute."""

from datetime import datetime

import pytest
from sqlalchemy import select

from module_admin.entity.do.dept_do import DeptDO
from modules.system.infrastructure.dept_repository import DeptRepository


@pytest.mark.asyncio
async def test_update_children_ancestors_updates_only_selected_rows(db_session):
    rows = [
        DeptDO(dept_name=f'batch {index}', parent_id=0, ancestors='0', status='0', del_flag='0') for index in range(3)
    ]
    db_session.add_all(rows)
    await db_session.flush()
    ids = [row.dept_id for row in rows]
    await DeptRepository(db_session).update_children_ancestors(
        [
            {'dept_id': ids[0], 'ancestors': '0,100'},
            {'dept_id': ids[1], 'ancestors': '0,100,101'},
        ]
    )
    result = dict(
        (await db_session.execute(select(DeptDO.dept_id, DeptDO.ancestors).where(DeptDO.dept_id.in_(ids)))).all()
    )
    assert result == {ids[0]: '0,100', ids[1]: '0,100,101', ids[2]: '0'}


@pytest.mark.asyncio
async def test_enabling_ancestors_does_not_touch_already_normal_records(db_session):
    old_time = datetime(2020, 1, 1)
    normal = DeptDO(dept_name='normal', status='0', update_time=old_time)
    disabled = DeptDO(dept_name='disabled', status='1', update_time=old_time)
    db_session.add_all([normal, disabled])
    await db_session.flush()
    await DeptRepository(db_session).update_status_normal([normal.dept_id, disabled.dept_id])
    rows = (await db_session.execute(select(DeptDO.dept_id, DeptDO.status, DeptDO.update_time))).all()
    by_id = {row.dept_id: row for row in rows}
    assert by_id[normal.dept_id].update_time == old_time
    assert by_id[disabled.dept_id].status == '0'
    assert by_id[disabled.dept_id].update_time > old_time
