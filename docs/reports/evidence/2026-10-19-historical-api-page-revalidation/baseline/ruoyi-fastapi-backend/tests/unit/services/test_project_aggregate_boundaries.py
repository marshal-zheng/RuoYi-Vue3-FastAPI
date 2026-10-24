from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from exceptions.exception import ResourceConflictException, ResourceNotFoundException
from module_admin.entity.do.project_do import ProjectDO
from module_admin.entity.do.project_topology_do import ProjectTopologyDO
from module_admin.entity.do.project_version_do import ProjectVersionDO
from module_admin.entity.vo.project_topology_vo import ProjectTopologyModel
from module_admin.entity.vo.project_version_vo import DeleteProjectVersionModel
from module_admin.entity.vo.project_vo import DeleteProjectModel
from modules.project.application.services.project_service import ProjectService
from modules.project.application.services.project_topology_service import ProjectTopologyService
from modules.project.application.services.project_version_service import ProjectVersionService
from modules.project.infrastructure.project_repository import ProjectRepository
from modules.project.infrastructure.project_topology_repository import ProjectTopologyRepository
from modules.project.infrastructure.project_version_repository import ProjectVersionRepository


@pytest_asyncio.fixture
async def sessions():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        for model in (ProjectDO, ProjectVersionDO, ProjectTopologyDO):
            await conn.run_sync(lambda c, m=model: m.__table__.create(c))
    async with factory() as db, db.begin():
        db.add_all(
            [
                ProjectDO(project_id=1, project_name='owned', del_flag='0'),
                ProjectDO(project_id=2, project_name='reference', del_flag='0'),
            ]
        )
        for id, project in [(1, 1), (2, 1), (3, 2)]:
            db.add(
                ProjectVersionDO(
                    version_id=id,
                    project_id=project,
                    version_number=f'v{id}',
                    version_name=f'version{id}',
                    is_locked='0',
                    del_flag='0',
                )
            )
            db.add(ProjectTopologyDO(project_id=project, version_id=id, topology_data={'nodes': [{'id': id}]}))
        db.add(ProjectTopologyDO(project_id=1, version_id=None, topology_data={'nodes': []}))
    try:
        yield factory
    finally:
        await engine.dispose()


def services(db):
    project = ProjectRepository(db)
    version = ProjectVersionRepository(db)
    topology = ProjectTopologyRepository(db)
    return SimpleNamespace(
        project=ProjectService(
            project_repo=project,
            version_repo=version,
            topology_repo=topology,
            device_repo=None,
            interface_repo=None,
            query_db=db,
        ),
        version=ProjectVersionService(version_repo=version, topology_repo=topology),
        topology=ProjectTopologyService(topology_repo=topology, project_repo=project, version_repo=version),
    )


@pytest.mark.asyncio
async def test_project_delete_cascades_versions_and_all_topologies_without_touching_reference(sessions):
    async with sessions() as db:
        await services(db).project.delete_project_services(DeleteProjectModel(project_ids='1', update_by='qa'))
    async with sessions() as db:
        assert (
            await db.execute(select(ProjectDO.__table__.c.del_flag).where(ProjectDO.project_id == 1))
        ).scalar_one() == '2'
        assert (
            await db.execute(select(ProjectVersionDO.__table__.c.del_flag).where(ProjectVersionDO.version_id == 1))
        ).scalar_one() == '2'
        assert (
            await db.execute(select(ProjectVersionDO.__table__.c.del_flag).where(ProjectVersionDO.version_id == 2))
        ).scalar_one() == '2'
        assert (
            await db.execute(
                select(func.count()).select_from(ProjectTopologyDO).where(ProjectTopologyDO.project_id == 1)
            )
        ).scalar_one() == 0
        assert (await db.get(ProjectDO, 2)).del_flag == '0'
        assert (await db.get(ProjectVersionDO, 3)).del_flag == '0'
        assert (await db.execute(select(func.count()).select_from(ProjectTopologyDO))).scalar_one() == 1
        with pytest.raises(ResourceNotFoundException):
            await services(db).topology.get_project_topology_services(1, 1)


@pytest.mark.asyncio
async def test_aggregate_cleanup_rolls_back_with_its_outer_transaction(sessions):
    async with sessions() as db:
        with pytest.raises(RuntimeError):
            async with db.begin():
                await ProjectRepository(db).soft_delete_batch([1], 'qa')
                raise RuntimeError('transaction failed')
    async with sessions() as db:
        assert (await db.get(ProjectDO, 1)).del_flag == '0'
        assert (await db.get(ProjectVersionDO, 1)).del_flag == '0'
        assert (await db.execute(select(func.count()).select_from(ProjectTopologyDO))).scalar_one() == 4


@pytest.mark.asyncio
async def test_version_delete_removes_its_topology_only(sessions):
    async with sessions() as db:
        await services(db).version.delete_project_version_services(
            DeleteProjectVersionModel(version_ids='1', update_by='qa')
        )
    async with sessions() as db:
        assert (
            await db.execute(select(ProjectVersionDO.__table__.c.del_flag).where(ProjectVersionDO.version_id == 1))
        ).scalar_one() == '2'
        assert (await db.get(ProjectVersionDO, 2)).del_flag == '0'
        assert (
            await db.execute(
                select(func.count()).select_from(ProjectTopologyDO).where(ProjectTopologyDO.version_id == 1)
            )
        ).scalar_one() == 0
        assert (await db.execute(select(func.count()).select_from(ProjectTopologyDO))).scalar_one() == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'project,version,error',
    [(99, 1, ResourceNotFoundException), (1, 3, ResourceNotFoundException), (1, 99, ResourceNotFoundException)],
)
async def test_topology_rejects_missing_or_mismatched_context(sessions, project, version, error):
    async with sessions() as db:
        with pytest.raises(error):
            await services(db).topology.save_project_topology_services(
                ProjectTopologyModel(project_id=project, version_id=version, topology_data={'nodes': []})
            )
        assert (await db.execute(select(func.count()).select_from(ProjectTopologyDO))).scalar_one() == 4


@pytest.mark.asyncio
async def test_lock_blocks_topology_and_project_delete_with_conflict(sessions):
    async with sessions() as db, db.begin():
        await db.execute(update(ProjectVersionDO).where(ProjectVersionDO.version_id == 1).values(is_locked='1'))
    async with sessions() as db:
        with pytest.raises(ResourceConflictException):
            await services(db).topology.save_project_topology_services(
                ProjectTopologyModel(project_id=1, version_id=1, topology_data={'nodes': []})
            )
        with pytest.raises(ResourceConflictException):
            await services(db).project.delete_project_services(DeleteProjectModel(project_ids='1'))
        assert (await db.get(ProjectDO, 1)).del_flag == '0'


@pytest.mark.asyncio
async def test_last_version_delete_returns_conflict(sessions):
    async with sessions() as db:
        with pytest.raises(ResourceConflictException):
            await services(db).version.delete_project_version_services(DeleteProjectVersionModel(version_ids='1,2'))
        assert (await db.get(ProjectVersionDO, 1)).del_flag == '0'


@pytest.mark.asyncio
async def test_valid_version_topology_can_still_be_saved(sessions):
    async with sessions() as db:
        await services(db).topology.save_project_topology_services(
            ProjectTopologyModel(project_id=1, version_id=1, topology_data={'nodes': [{'id': 'updated'}]})
        )
    async with sessions() as db:
        result = await services(db).topology.get_project_topology_services(1, 1)
        assert result['topologyData']['nodes'] == [{'id': 'updated'}]
