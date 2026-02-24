from unittest.mock import AsyncMock

import pytest

from module_admin.entity.vo.project_version_vo import ProjectVersionModel
from modules.project.application.services.project_version_service import ProjectVersionService


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
