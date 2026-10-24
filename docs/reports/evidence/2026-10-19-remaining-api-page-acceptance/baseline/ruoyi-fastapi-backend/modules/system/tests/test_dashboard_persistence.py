import asyncio
from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from exceptions.exception import ResourceNotFoundException
from exceptions.handle import handle_exception
from module_admin.entity.do.dashboard_do import DashboardDO, DashboardVersionDO
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.api.dashboard_controller import dashboard_controller, dashboard_service
from modules.system.application.services.dashboard_service import DashboardService
from modules.system.infrastructure.dashboard_repository import DashboardRepository


def document(title='Layout'):
    return {'schemaVersion': 2, 'title': title, 'panels': []}


def actor(user_id=11, permissions=()):
    return CurrentUserModel(
        permissions=list(permissions),
        roles=[],
        user={'userId': user_id, 'userName': f'user-{user_id}'},
    )


@pytest_asyncio.fixture
async def api(tmp_path):
    engine = create_async_engine(f'sqlite+aiosqlite:///{tmp_path}/dashboard.db')
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync: DashboardDO.metadata.create_all(
                sync,
                tables=[DashboardDO.__table__, DashboardVersionDO.__table__],
            )
        )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    auth = {'user': actor()}

    async def project_detail(project_id):
        if project_id != 7:
            raise ResourceNotFoundException(user_message='工程不存在')
        return {'projectId': 7}

    async def service():
        async with sessions() as session:
            yield DashboardService(DashboardRepository(session), project_detail)

    app = FastAPI()
    handle_exception(app)
    app.include_router(dashboard_controller)
    app.dependency_overrides[get_current_user] = lambda: auth['user']
    app.dependency_overrides[dashboard_service] = service
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield SimpleNamespace(client=client, auth=auth, sessions=sessions)
    await engine.dispose()


@pytest.mark.asyncio
async def test_conditional_crud_and_immutable_versions(api):
    url = '/system/dashboard/account/monitor-server'
    assert (await api.client.get(url)).json() is None
    first = await api.client.put(url, json={'document': document(), 'expectedRevision': None})
    assert first.status_code == 200
    assert first.json()['revision'] == 1
    second = await api.client.put(url, json={'document': document('New'), 'expectedRevision': 1})
    assert second.status_code == 200
    assert second.json()['revision'] == 2
    assert second.json()['ownerId'] == 11
    async with api.sessions() as session:
        versions = (
            (await session.execute(select(DashboardVersionDO).order_by(DashboardVersionDO.revision))).scalars().all()
        )
        assert [row.document['title'] for row in versions] == ['Layout', 'New']
    stale = await api.client.delete(url, params={'expectedRevision': 1})
    assert stale.status_code == 409
    assert stale.json()['errors'][0]['remote']['revision'] == 2
    assert (await api.client.delete(url, params={'expectedRevision': 2})).status_code == 204
    assert (await api.client.get(url)).json() is None
    async with api.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(DashboardVersionDO)) == 0


@pytest.mark.asyncio
async def test_account_isolation_and_caller_cannot_choose_owner(api):
    url = '/system/dashboard/account/monitor-server'
    await api.client.put(url, json={'document': document('Private'), 'expectedRevision': None})
    api.auth['user'] = actor(22, ('*:*:*',))
    assert (await api.client.get(url)).json() is None
    forged = await api.client.put(url, json={'document': document(), 'expectedRevision': 1, 'ownerId': 11})
    assert forged.status_code == 422
    own = await api.client.put(url, json={'document': document('Own'), 'expectedRevision': None})
    assert own.json()['ownerId'] == 22
    api.auth['user'] = actor()
    assert (await api.client.get(url)).json()['document']['title'] == 'Private'


@pytest.mark.asyncio
async def test_scene_permissions_and_project_existence(api):
    url = '/system/dashboard/scene/7'
    assert (await api.client.get(url)).status_code == 403
    api.auth['user'] = actor(11, ('project:project:query',))
    assert (await api.client.get(url)).status_code == 200
    assert (await api.client.put(url, json={'document': document(), 'expectedRevision': None})).status_code == 403
    permissions = ('project:project:query', 'project:project:edit')
    api.auth['user'] = actor(11, permissions)
    assert (await api.client.put(url, json={'document': document(), 'expectedRevision': None})).status_code == 200
    api.auth['user'] = actor(22, permissions)
    shared = await api.client.get(url)
    assert shared.json()['ownerId'] == 11
    assert (await api.client.put(url, json={'document': document('Shared'), 'expectedRevision': 1})).json()[
        'revision'
    ] == 2
    assert (await api.client.get('/system/dashboard/scene/8')).status_code == 404
    assert (await api.client.get('/system/dashboard/scene/07')).status_code == 422


@pytest.mark.asyncio
async def test_concurrent_saves_have_one_winner_and_one_conflict(api):
    url = '/system/dashboard/account/race'
    await api.client.put(url, json={'document': document(), 'expectedRevision': None})
    results = await asyncio.gather(
        *[api.client.put(url, json={'document': document(title), 'expectedRevision': 1}) for title in ('A', 'B')]
    )
    assert sorted(result.status_code for result in results) == [200, 409]
    winner = next(result.json() for result in results if result.status_code == 200)
    loser = next(result.json() for result in results if result.status_code == 409)
    assert loser['errors'][0]['remote'] == winner
    async with api.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(DashboardVersionDO)) == 2


@pytest.mark.asyncio
async def test_duplicate_create_and_stale_recreation_are_conflicts(api):
    url = '/system/dashboard/account/create'
    payload = {'document': document(), 'expectedRevision': None}
    assert (await api.client.put(url, json=payload)).status_code == 200
    assert (await api.client.put(url, json=payload)).status_code == 409
    await api.client.delete(url, params={'expectedRevision': 1})
    response = await api.client.put(url, json={**payload, 'expectedRevision': 1})
    assert response.status_code == 409
    assert response.json()['errors'][0]['remote'] is None
    recreated = await api.client.put(url, json=payload)
    assert recreated.status_code == 200
    assert recreated.json()['revision'] == 3
    stale = await api.client.put(url, json={**payload, 'expectedRevision': 1})
    assert stale.status_code == 409
    assert stale.json()['errors'][0]['remote']['revision'] == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'bad',
    [
        {'schemaVersion': 1, 'panels': []},
        {'schemaVersion': 2, 'panels': [{'id': 'a', 'widget': 'zx.stat'}]},
        {'schemaVersion': 2, 'panels': [], 'description': 'x' * (1024 * 1024)},
    ],
)
async def test_invalid_or_oversized_documents_are_rejected(api, bad):
    response = await api.client.put('/system/dashboard/account/bad', json={'document': bad, 'expectedRevision': None})
    assert response.status_code == 422
    assert (await api.client.get('/system/dashboard/account/bad')).json() is None
