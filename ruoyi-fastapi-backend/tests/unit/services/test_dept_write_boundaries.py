"""Department hierarchy and write boundaries, independent of HTTP validation."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from exceptions.exception import PermissionException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.vo.dept_vo import DeptModel
from modules.system.application.services.dept_service import DeptService


def node(dept_id, parent_id=0, ancestors='0', status='0'):
    return DeptDO(
        dept_id=dept_id,
        parent_id=parent_id,
        ancestors=ancestors,
        dept_name=f'Dept {dept_id}',
        order_num=1,
        status=status,
        del_flag='0',
        create_by='original',
    )


@pytest.fixture
def tree():
    rows = {1: node(1), 2: node(2, 1, '0,1'), 3: node(3, 2, '0,1,2'), 4: node(4), 5: node(5, 4, '0,4')}
    repo = MagicMock()
    repo.find_by_id = AsyncMock(side_effect=lambda dept_id: rows.get(dept_id))
    repo.find_by_parent_and_name = AsyncMock(return_value=None)
    repo.find_with_filters = AsyncMock(
        side_effect=lambda *, dept_id, data_scope_sql: [rows[dept_id]] if dept_id in {2, 3} and data_scope_sql else []
    )
    repo.find_children = AsyncMock(
        side_effect=lambda dept_id: [row for row in rows.values() if str(dept_id) in row.ancestors.split(',')]
    )
    repo.update_children_ancestors = AsyncMock()
    repo.update_status_normal = AsyncMock()
    repo.count_normal_children = AsyncMock(return_value=0)
    repo.update = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda row: row)
    service = DeptService(repo, None)
    service._invalidate_dept_cache = AsyncMock()
    return service, repo, rows


@pytest.mark.asyncio
async def test_missing_target_cannot_succeed(tree):
    service, repo, _ = tree
    with pytest.raises(ResourceNotFoundException):
        await service.edit_dept_services(DeptModel(dept_id=99, dept_name='missing'))
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_parent_cannot_be_persisted(tree):
    service, repo, rows = tree
    with pytest.raises(ResourceNotFoundException):
        await service.edit_dept_services(DeptModel(dept_id=2, parent_id=99, dept_name='move', order_num=1))
    assert rows[2].parent_id == 1
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('parent_id', [2, 3])
async def test_self_or_descendant_parent_is_rejected_before_subtree_write(tree, parent_id):
    service, repo, rows = tree
    with pytest.raises(ValidationException):
        await service.edit_dept_services(DeptModel(dept_id=2, parent_id=parent_id, dept_name='move', order_num=1))
    assert rows[2].parent_id == 1
    repo.update_children_ancestors.assert_not_awaited()
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_cycle_check_follows_parent_links_instead_of_trusting_stored_ancestors(tree):
    service, repo, rows = tree
    rows[3].ancestors = '0'
    with pytest.raises(ValidationException):
        await service.edit_dept_services(DeptModel(dept_id=2, parent_id=3, dept_name='move', order_num=1))
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['add', 'edit'])
@pytest.mark.parametrize('parent_id', [0, 4])
async def test_restricted_user_cannot_place_department_outside_scope(tree, operation, parent_id):
    service, repo, _ = tree
    data = DeptModel(
        parent_id=parent_id, dept_name='scoped', order_num=0, **({'dept_id': 2} if operation == 'edit' else {})
    )
    with pytest.raises(PermissionException):
        await getattr(service, f'{operation}_dept_services')(data, enforce_data_scope=True, data_scope_sql='scoped')
    repo.add.assert_not_awaited()
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_unchanged_or_omitted_parent_does_not_require_parent_permission(tree):
    service, repo, rows = tree
    for data in [DeptModel(dept_id=2, dept_name='renamed'), DeptModel(dept_id=2, parent_id=1, order_num=0)]:
        await service.edit_dept_services(data, enforce_data_scope=True, data_scope_sql='scoped')
    assert rows[2].dept_name == 'renamed'
    assert rows[2].order_num == 0
    assert rows[2].parent_id == 1
    repo.find_with_filters.assert_not_awaited()


@pytest.mark.asyncio
async def test_move_updates_descendant_ancestry_and_preserves_unspecified_fields(tree):
    service, repo, rows = tree
    await service.edit_dept_services(DeptModel(dept_id=2, parent_id=5))
    assert rows[2].parent_id == 5
    assert rows[2].ancestors == '0,4,5'
    assert rows[2].dept_name == 'Dept 2'
    assert rows[2].status == '0'
    repo.update_children_ancestors.assert_awaited_once_with([{'dept_id': 3, 'ancestors': '0,4,5,2'}])


@pytest.mark.asyncio
async def test_root_edit_and_admin_root_placement(tree):
    service, repo, rows = tree
    await service.edit_dept_services(DeptModel(dept_id=1, dept_name='root'))
    assert rows[1].parent_id == 0 and rows[1].ancestors == '0'
    await service.edit_dept_services(DeptModel(dept_id=2, parent_id=0))
    assert rows[2].ancestors == '0'
    await service.add_dept_services(DeptModel(parent_id=0, dept_name='new root', order_num=0))
    assert repo.add.call_args.args[0].ancestors == '0'


@pytest.mark.asyncio
async def test_partial_update_uses_allowlist_and_clears_contacts(tree):
    service, _repo, rows = tree
    old_time = datetime(2020, 1, 1)
    rows[2].phone = '13800000000'
    await service.edit_dept_services(
        DeptModel(
            dept_id=2,
            phone=None,
            del_flag='2',
            ancestors='forged',
            create_by='forged',
            create_time=old_time,
            update_by='operator',
        )
    )
    assert rows[2].phone is None
    assert rows[2].del_flag == '0'
    assert rows[2].ancestors == '0,1'
    assert rows[2].create_by == 'original'
    assert rows[2].create_time != old_time
    assert rows[2].update_by == 'operator'


@pytest.mark.asyncio
async def test_create_derives_ancestry_and_drops_identity_and_delete_flag(tree):
    service, repo, _ = tree
    await service.add_dept_services(
        DeptModel(
            dept_id=999,
            parent_id=2,
            dept_name='new',
            order_num=0,
            ancestors='forged',
            del_flag='2',
            create_by='operator',
        )
    )
    row = repo.add.call_args.args[0]
    assert row.dept_id is None
    assert row.del_flag in (None, '0')
    assert row.ancestors == '0,1,2'
    assert row.create_by == 'operator'


@pytest.mark.asyncio
async def test_disabled_parent_still_blocks_create_and_edit_can_enable_ancestors(tree):
    service, repo, rows = tree
    rows[1].status = '1'
    with pytest.raises(ValidationException):
        await service.add_dept_services(DeptModel(parent_id=1, dept_name='new', order_num=0))
    await service.edit_dept_services(DeptModel(dept_id=2, status='0'))
    repo.update_status_normal.assert_awaited_once_with([1])


@pytest.mark.asyncio
async def test_active_children_still_block_disable(tree):
    service, repo, rows = tree
    repo.count_normal_children.return_value = 1
    with pytest.raises(ValidationException):
        await service.edit_dept_services(DeptModel(dept_id=2, status='1'))
    assert rows[2].status == '0'
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_status_only_write_passes_existing_command_validation():
    DeptModel(dept_id=2, status='1').validate_fields()


@pytest.mark.asyncio
async def test_enabling_cannot_change_disabled_ancestor_outside_scope(tree):
    service, repo, rows = tree
    rows[1].status = rows[2].status = '1'
    with pytest.raises(PermissionException):
        await service.edit_dept_services(
            DeptModel(dept_id=2, status='0'), enforce_data_scope=True, data_scope_sql='scoped'
        )
    assert rows[2].status == '1'
    repo.update.assert_not_awaited()
    repo.update_status_normal.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_department_move_enables_new_ancestors_with_omitted_status(tree):
    service, repo, rows = tree
    rows[4].status = '1'
    await service.edit_dept_services(DeptModel(dept_id=2, parent_id=4))
    repo.update_status_normal.assert_awaited_once_with([4])


@pytest.mark.asyncio
async def test_move_cannot_enable_indirect_ancestor_outside_scope(tree):
    service, repo, rows = tree
    # Parent 3 is authorized; its ancestor 4 is disabled and outside scope.
    rows[3].parent_id, rows[3].ancestors = 4, '0,4'
    rows[4].status = '1'
    with pytest.raises(PermissionException):
        await service.edit_dept_services(
            DeptModel(dept_id=2, parent_id=3), enforce_data_scope=True, data_scope_sql='scoped'
        )
    assert rows[2].parent_id == 1
    repo.update_children_ancestors.assert_not_awaited()
    repo.update.assert_not_awaited()
