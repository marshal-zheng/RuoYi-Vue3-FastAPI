from unittest.mock import AsyncMock

import pytest

from module_admin.entity.vo.project_version_vo import ProjectVersionPageQueryModel
from module_admin.entity.vo.project_version_vo import ProjectVersionModel
from modules.project.application.services.project_version_service import ProjectVersionService
from utils.page_util import PageResponseModel


@pytest.mark.asyncio
async def test_edit_project_version_uses_repository_update():
    version = type(
        'VersionEntity',
        (),
        {
            'version_id': 1,
            'project_id': 10,
            'version_number': 'v1.0.0',
            'version_name': '原版本',
            'description': 'old',
            'is_locked': '0',
        },
    )()

    fake_repo = type(
        'FakeProjectVersionRepo',
        (),
        {
            'find_by_id': AsyncMock(return_value=version),
            'check_version_number_unique': AsyncMock(return_value=True),
            'update': AsyncMock(return_value=version),
        },
    )()
    fake_topology_repo = type('FakeProjectTopologyRepo', (), {})()
    service = ProjectVersionService(version_repo=fake_repo, topology_repo=fake_topology_repo)

    payload = ProjectVersionModel(
        versionId=1,
        projectId=10,
        versionNumber='v1.0.1',
        versionName='新版本',
        description='new',
    )
    result = await service.edit_project_version_services(payload)

    assert result.is_success is True
    assert version.version_number == 'v1.0.1'
    assert version.version_name == '新版本'
    assert version.description == 'new'
    fake_repo.update.assert_awaited_once_with(version)


@pytest.mark.asyncio
async def test_get_project_version_list_uses_page_contract():
    paged_result = PageResponseModel(
        items=[{'versionId': 7, 'versionName': 'v1'}],
        page=3,
        pageSize=15,
        total=9,
    )
    fake_repo = type(
        'FakeProjectVersionRepo',
        (),
        {
            'paginate_with_filters': AsyncMock(return_value=paged_result),
        },
    )()
    fake_topology_repo = type('FakeProjectTopologyRepo', (), {})()
    service = ProjectVersionService(version_repo=fake_repo, topology_repo=fake_topology_repo)

    result = await service.get_project_version_list_services(
        ProjectVersionPageQueryModel(page=3, pageSize=15, projectId=10),
        is_page=True,
    )

    assert result is paged_result
    assert result.model_dump(by_alias=True) == {
        'items': [{'versionId': 7, 'versionName': 'v1'}],
        'page': 3,
        'pageSize': 15,
        'total': 9,
    }
    assert not hasattr(result, 'rows')
    fake_repo.paginate_with_filters.assert_awaited_once_with(
        page=3,
        page_size=15,
        project_id=10,
        version_name=None,
        version_number=None,
        begin_time=None,
        end_time=None,
    )
