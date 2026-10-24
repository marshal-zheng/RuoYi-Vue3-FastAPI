"""DeptService consistency at controlled repository visibility boundaries.

The service and QueryCache are real. The repository makes read snapshots,
outer commit and rollback deterministic without a live database or Redis.
"""

import asyncio
import fnmatch

import pytest

from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.vo.dept_vo import DeptModel
from modules.system.application.services.dept_service import DeptService
from utils.query_cache import QueryCache


def department(dept_id=100, parent_id=0, name='department old'):
    return DeptDO(
        dept_id=dept_id,
        parent_id=parent_id,
        ancestors='0' if parent_id == 0 else f'0,{parent_id}',
        dept_name=name,
        order_num=0,
        status='0',
        del_flag='0',
    )


class MemoryRedis:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, ttl, value):
        self.values[key] = value

    async def keys(self, pattern):
        return [key for key in self.values if fnmatch.fnmatch(key, pattern)]

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)


class ScheduledRepository:
    def __init__(self, committed):
        self.committed = committed
        self.pending = {}
        self.calls = []
        self.block_next_tree = False
        self.snapshot_loaded = asyncio.Event()
        self.release_snapshot = asyncio.Event()

    def visible_rows(self):
        return {**self.committed, **self.pending}

    async def find_by_id(self, dept_id):
        return self.visible_rows().get(dept_id)

    async def find_by_parent_and_name(self, **kwargs):
        return None

    async def add(self, row):
        row.dept_id = 101
        self.pending[row.dept_id] = row
        return row

    async def find_all_for_tree(self, **kwargs):
        self.calls.append(('tree', kwargs))
        snapshot = list(self.visible_rows().values())
        if self.block_next_tree:
            self.block_next_tree = False
            self.snapshot_loaded.set()
            await self.release_snapshot.wait()
        return snapshot

    async def find_for_edit_option(self, **kwargs):
        self.calls.append(('exclude', kwargs))
        return [row for row in self.visible_rows().values() if row.dept_id != kwargs['exclude_dept_id']]

    async def find_with_filters(self, **kwargs):
        self.calls.append(('list', kwargs))
        return list(self.visible_rows().values())

    async def find_active_by_id(self, dept_id):
        self.calls.append(('detail', {'dept_id': dept_id}))
        return self.visible_rows().get(dept_id)

    def commit(self):
        self.committed.update(self.pending)
        self.pending.clear()

    def rollback(self):
        self.pending.clear()


@pytest.fixture
def shared_query_cache(monkeypatch):
    cache = QueryCache(MemoryRedis(), is_async=True)
    monkeypatch.setattr('utils.query_cache._query_cache', cache)
    return cache


async def read_department(service, kind, scope):
    if kind == 'tree':
        result = await service.get_dept_tree_services(DeptModel(dept_name='department'), scope)
        return result[0]['label']
    if kind == 'exclude':
        result = await service.get_dept_for_edit_option_services(DeptModel(dept_id=999), scope)
        return result[0]['deptName']
    if kind == 'list':
        result = await service.get_dept_list_services(DeptModel(dept_id=100, dept_name='department', status='0'), scope)
        return result[0]['deptName']
    result = await service.dept_detail_services(100)
    return result.dept_name


@pytest.mark.parametrize('kind', ['tree', 'exclude', 'list', 'detail'])
async def test_independent_read_observes_latest_committed_department(shared_query_cache, kind):
    committed = {100: department()}
    repo = ScheduledRepository(committed)
    scope = object()
    assert await read_department(DeptService(repo, None), kind, scope) == 'department old'

    committed[100] = department(name='department new')

    assert await read_department(DeptService(repo, None), kind, scope) == 'department new'
    expected = {
        'tree': {'dept_name': 'department', 'data_scope_sql': scope},
        'exclude': {'exclude_dept_id': 999, 'data_scope_sql': scope},
        'list': {'dept_id': 100, 'status': '0', 'dept_name': 'department', 'data_scope_sql': scope},
        'detail': {'dept_id': 100},
    }
    assert repo.calls == [(kind, expected[kind]), (kind, expected[kind])]


def contains_department(nodes, dept_id):
    return any(node['id'] == dept_id or contains_department(node.get('children', []), dept_id) for node in nodes)


@pytest.mark.parametrize('post_commit_delete', [False, True], ids=['pre-commit-delete', 'also-post-commit-delete'])
async def test_in_flight_old_snapshot_cannot_poison_later_reads(shared_query_cache, post_commit_delete):
    committed = {100: department()}
    reader_repo = ScheduledRepository(committed)
    reader = DeptService(reader_repo, None)
    await reader.get_dept_tree_services(DeptModel(), 'True')

    writer_repo = ScheduledRepository(committed)
    result = await DeptService(writer_repo, None).add_dept_services(
        DeptModel(parent_id=100, dept_name='department child', order_num=0, status='0')
    )
    assert result.is_success

    reader_repo.block_next_tree = True
    old_read = asyncio.create_task(reader.get_dept_tree_services(DeptModel(), 'True'))
    try:
        await asyncio.wait_for(reader_repo.snapshot_loaded.wait(), 1)
        writer_repo.commit()
        if post_commit_delete:
            await shared_query_cache.delete_pattern(f'{shared_query_cache.key_prefix}:dept:*')
    finally:
        reader_repo.release_snapshot.set()
    assert not contains_department(await old_read, 101)

    independent = await DeptService(ScheduledRepository(committed), None).get_dept_tree_services(DeptModel(), 'True')
    assert contains_department(independent, 101)


async def test_detail_in_rolled_back_transaction_is_not_published_to_other_requests(shared_query_cache):
    committed = {100: department()}
    writer_repo = ScheduledRepository(committed)
    writer_repo.pending[100] = department(name='department uncommitted')
    own_detail = await DeptService(writer_repo, None).dept_detail_services(100)
    assert own_detail.dept_name == 'department uncommitted'

    writer_repo.rollback()

    independent = await DeptService(ScheduledRepository(committed), None).dept_detail_services(100)
    assert independent.dept_name == 'department old'
