from __future__ import annotations

from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient

from container.wiring import build_container
from config.get_db import get_db
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from module_admin.controller.protocol_controller import protocolController
from modules.scheduler.api.job_controller import jobController
from modules.identity.application.services.login_service import LoginService
from modules.identity.ports import get_current_user
from modules.project.api.project_controller import projectController
from modules.system.api.dependencies import provide_system_mediator
from modules.system.api.notice_controller import noticeController
from modules.system.api.user_controller import userController
from modules.system.application.commands import AddNoticeCommand, EditNoticeCommand
from modules.system.application.commands import ImportUsersCommand
from modules.system.application.contracts import CommandResult
from modules.system.application.queries import GetNoticeDetailQuery
from module_generator.controller.gen_controller import genController


class _FakeProjectService:
    def __init__(self) -> None:
        self._projects = {
            101: {
                'projectId': 101,
                'projectName': '演示工程',
                'projectDesc': 'demo project',
            }
        }

    async def add_project(self, project, operator: str | None = None):
        project_id = 101
        self._projects[project_id] = {
            'projectId': project_id,
            'projectName': project.project_name,
            'projectDesc': project.project_desc,
            'updateBy': operator,
        }
        return SimpleNamespace(message='新增成功', result={'projectId': project_id, 'versionId': 201})

    async def edit_project(self, project, operator: str | None = None):
        self._projects[project.project_id] = {
            'projectId': project.project_id,
            'projectName': project.project_name,
            'projectDesc': project.project_desc,
            'updateBy': operator,
        }
        return SimpleNamespace(message='更新成功', result={'projectId': project.project_id})

    async def get_project_detail(self, project_id: int):
        return self._projects[project_id]

    async def get_project_list(self, _query, is_page: bool = True):
        assert is_page is True
        return {
            'items': list(self._projects.values()),
            'total': len(self._projects),
            'page': 1,
            'pageSize': 10,
        }

    async def import_projects_from_zip(self, _file_bytes: bytes, _operator: str):
        return {
            'successCount': 1,
            'failedCount': 1,
            'details': [
                {
                    'fileName': 'ok.json',
                    'status': 'success',
                    'projectId': 101,
                    'versionId': 201,
                },
                {
                    'fileName': 'bad.json',
                    'status': 'failed',
                    'message': '导入失败',
                },
            ],
        }


class _FakeNoticeMediator:
    def __init__(self) -> None:
        self._notice = {
            'noticeId': 88,
            'noticeTitle': '初始公告',
            'noticeType': '1',
            'status': '0',
            'noticeContent': 'content',
        }

    async def send(self, request):
        if isinstance(request, ImportUsersCommand):
            return CommandResult(
                success=True,
                status='imported',
                data={
                    'results': [
                        {
                            'itemId': 'admin',
                            'success': True,
                            'rowNumber': 2,
                            'userName': 'admin',
                            'action': 'updated',
                        },
                        {
                            'itemId': 'missing-user',
                            'success': False,
                            'rowNumber': 3,
                            'userName': 'missing-user',
                            'action': 'skipped',
                            'error': {
                                'errorCode': 'USER_IMPORT_FAILED',
                                'title': '用户导入失败',
                                'detail': '部门不存在',
                            },
                        },
                    ],
                    'summary': {'total': 2, 'succeeded': 1, 'failed': 1},
                },
            )

        if isinstance(request, AddNoticeCommand):
            self._notice = {
                'noticeId': 88,
                'noticeTitle': request.notice.notice_title,
                'noticeType': request.notice.notice_type,
                'status': request.notice.status,
                'noticeContent': request.notice.notice_content,
            }
            return CommandResult(success=True, status='created', data={'message': '新增成功', 'noticeId': 88})

        if isinstance(request, EditNoticeCommand):
            self._notice = {
                'noticeId': request.notice.notice_id,
                'noticeTitle': request.notice.notice_title,
                'noticeType': request.notice.notice_type,
                'status': request.notice.status,
                'noticeContent': request.notice.notice_content,
            }
            return CommandResult(success=True, status='updated', data={'message': '更新成功'})

        raise AssertionError(f'unexpected command: {type(request)!r}')

    async def query(self, request):
        if isinstance(request, GetNoticeDetailQuery):
            return self._notice
        raise AssertionError(f'unexpected query: {type(request)!r}')


class _FakeGenTableService:
    async def get_gen_db_table_list_by_name_services(self, table_names: list[str]):
        return [SimpleNamespace(table_name=table_name) for table_name in table_names]

    async def import_gen_table_services(self, gen_table_list, _current_user):
        return SimpleNamespace(
            message='导入成功',
            result={
                'tableNames': [table.table_name for table in gen_table_list],
                'importedCount': len(gen_table_list),
            },
        )

    async def validate_edit(self, _edit_gen_table):
        return None

    async def edit_gen_table_services(self, _edit_gen_table):
        return SimpleNamespace(message='更新成功')

    async def create_table_services(self, _sql: str, _current_user):
        return SimpleNamespace(message='创建表成功', result={'tableNames': ['demo_table'], 'createdCount': 1})

    async def get_gen_table_by_id_services(self, table_id: int):
        return {
            'tableId': table_id,
            'tableName': 'demo_table',
            'tableComment': '演示表',
        }

    async def get_gen_table_all_services(self):
        return [{'tableId': 7, 'tableName': 'demo_table'}]

    async def sync_db_services(self, table_name: str):
        return SimpleNamespace(message='同步成功', result={'tableId': 7, 'tableName': table_name})


class _FakeGenTableColumnService:
    async def get_gen_table_column_list_by_table_id_services(self, table_id: int):
        return [
            {
                'columnId': 1,
                'tableId': table_id,
                'columnName': 'id',
                'columnComment': '主键',
            }
        ]


class _FakeJobService:
    def __init__(self) -> None:
        self._jobs = {
            301: {
                'jobId': 301,
                'jobName': '演示任务',
                'jobGroup': 'DEFAULT',
                'invokeTarget': 'demo.job.run()',
                'cronExpression': '0/5 * * * * ?',
                'status': '0',
                'updateBy': 'admin',
            }
        }

    async def add_job_services(self, job):
        job_id = 301
        self._jobs[job_id] = {
            'jobId': job_id,
            'jobName': job.job_name,
            'jobGroup': job.job_group,
            'invokeTarget': job.invoke_target,
            'cronExpression': job.cron_expression,
            'status': job.status,
            'updateBy': job.update_by,
        }
        return SimpleNamespace(message='新增成功', result={'jobId': job_id})

    async def edit_job_services(self, job):
        current = dict(self._jobs[job.job_id])
        if job.job_name is not None:
            current['jobName'] = job.job_name
        if job.job_group is not None:
            current['jobGroup'] = job.job_group
        if job.invoke_target is not None:
            current['invokeTarget'] = job.invoke_target
        if job.cron_expression is not None:
            current['cronExpression'] = job.cron_expression
        if job.status is not None:
            current['status'] = job.status
        current['updateBy'] = job.update_by
        self._jobs[job.job_id] = current
        return SimpleNamespace(message='更新成功', result={'jobId': job.job_id})

    async def change_job_status_services(self, job):
        return await self.edit_job_services(job)

    async def job_detail_services(self, job_id: int):
        return self._jobs[job_id]


class _FakeProtocolService:
    def __init__(self) -> None:
        self._protocols = {
            501: {
                'protocolId': 501,
                'protocolName': '导入协议',
                'protocolType': 'CAN',
                'status': '0',
            }
        }

    async def import_protocol_services(self, _file, protocol_name: str | None, _operator: str):
        protocol_id = 501
        self._protocols[protocol_id] = {
            'protocolId': protocol_id,
            'protocolName': protocol_name or '导入协议',
            'protocolType': 'CAN',
            'status': '0',
        }
        return SimpleNamespace(
            message='导入成功',
            result={'protocolId': protocol_id, 'protocolName': protocol_name or '导入协议', 'protocolType': 'CAN'},
        )

    async def get_protocol_detail(self, protocol_id: int):
        return self._protocols[protocol_id]


def _build_current_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['*:*:*'],
        roles=['admin'],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='管理员',
            deptId=1,
            status='0',
            delFlag='0',
            role=[RoleModel(roleKey='admin', roleName='管理员')],
        ),
    )


async def _override_current_user() -> CurrentUserModel:
    return _build_current_user()


async def _override_db():
    yield None


@pytest_asyncio.fixture
async def contract_client():
    app = FastAPI()
    container = build_container()
    container.override('project_service', lambda _session: _FakeProjectService())
    container.override('gen_table_service', lambda _session: _FakeGenTableService())
    container.override('gen_table_column_service', lambda _session: _FakeGenTableColumnService())
    container.override('job_service', lambda _session: _FakeJobService())
    container.override('protocol_service', lambda _session: _FakeProtocolService())
    app.state.container = container
    app.include_router(projectController)
    app.include_router(noticeController)
    app.include_router(genController)
    app.include_router(jobController)
    app.include_router(protocolController)
    app.include_router(userController)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[LoginService.get_current_user] = _override_current_user
    app.dependency_overrides[provide_system_mediator] = lambda: _FakeNoticeMediator()

    async with AsyncClient(app=app, base_url='http://testserver') as client:
        yield client


@pytest.mark.asyncio
async def test_project_create_returns_created_resource(contract_client: AsyncClient):
    response = await contract_client.post(
        '/project',
        json={
            'projectName': '演示工程',
            'projectDesc': 'demo project',
        },
    )

    assert response.status_code == 201
    assert response.headers['Location'] == 'http://testserver/project/101'
    assert response.json() == {
        'projectId': 101,
        'versionId': 201,
        'projectName': '演示工程',
        'projectDesc': 'demo project',
        'updateBy': 'admin',
    }


@pytest.mark.asyncio
async def test_project_update_returns_updated_resource(contract_client: AsyncClient):
    response = await contract_client.put(
        '/project',
        json={
            'projectId': 101,
            'projectName': '已更新工程',
            'projectDesc': 'updated project',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'projectId': 101,
        'projectName': '已更新工程',
        'projectDesc': 'updated project',
        'updateBy': 'admin',
    }


@pytest.mark.asyncio
async def test_project_list_returns_page_contract_without_rows(contract_client: AsyncClient):
    response = await contract_client.get('/project/list?page=1&pageSize=10')

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        'items': [
            {
                'projectId': 101,
                'projectName': '演示工程',
                'projectDesc': 'demo project',
            }
        ],
        'total': 1,
        'page': 1,
        'pageSize': 10,
    }
    assert 'rows' not in payload


@pytest.mark.asyncio
async def test_project_import_batch_returns_results_and_summary(contract_client: AsyncClient):
    response = await contract_client.post(
        '/project/import/batch',
        files={'file': ('projects.zip', b'zip-binary', 'application/zip')},
    )

    assert response.status_code == 200
    assert response.json() == {
        'results': [
            {
                'itemId': 101,
                'success': True,
                'projectId': 101,
                'versionId': 201,
                'fileName': 'ok.json',
            },
            {
                'itemId': 'bad.json',
                'success': False,
                'fileName': 'bad.json',
                'error': {
                    'errorCode': None,
                    'title': '导入失败',
                    'detail': '导入失败',
                },
            },
        ],
        'summary': {'total': 2, 'succeeded': 1, 'failed': 1},
    }


@pytest.mark.asyncio
async def test_notice_create_returns_created_resource(contract_client: AsyncClient):
    response = await contract_client.post(
        '/system/notice',
        json={
            'noticeTitle': '发布公告',
            'noticeType': '1',
            'status': '0',
            'noticeContent': '内容',
        },
    )

    assert response.status_code == 201
    assert response.headers['Location'] == 'http://testserver/system/notice/88'
    assert response.json() == {
        'noticeId': 88,
        'noticeTitle': '发布公告',
        'noticeType': '1',
        'status': '0',
        'noticeContent': '内容',
    }


@pytest.mark.asyncio
async def test_notice_update_returns_updated_resource(contract_client: AsyncClient):
    response = await contract_client.put(
        '/system/notice',
        json={
            'noticeId': 88,
            'noticeTitle': '已更新公告',
            'noticeType': '1',
            'status': '0',
            'noticeContent': '更新内容',
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'noticeId': 88,
        'noticeTitle': '已更新公告',
        'noticeType': '1',
        'status': '0',
        'noticeContent': '更新内容',
    }


@pytest.mark.asyncio
async def test_user_import_returns_batch_contract_without_success_message(contract_client: AsyncClient):
    response = await contract_client.post(
        '/system/user/importData',
        params={'updateSupport': 'true'},
        files={
            'file': (
                'users.xlsx',
                b'binary-data',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        'results': [
            {
                'itemId': 'admin',
                'success': True,
                'rowNumber': 2,
                'userName': 'admin',
                'action': 'updated',
            },
            {
                'itemId': 'missing-user',
                'success': False,
                'rowNumber': 3,
                'userName': 'missing-user',
                'action': 'skipped',
                'error': {
                    'errorCode': 'USER_IMPORT_FAILED',
                    'title': '用户导入失败',
                    'detail': '部门不存在',
                },
            },
        ],
        'summary': {'total': 2, 'succeeded': 1, 'failed': 1},
    }
    assert 'message' not in payload
    assert 'msg' not in payload
    assert set(payload['results'][1]['error']) == {'errorCode', 'title', 'detail'}


@pytest.mark.asyncio
async def test_gen_detail_uses_columns_field(contract_client: AsyncClient):
    response = await contract_client.get('/tool/gen/7')

    assert response.status_code == 200
    assert 'columns' in response.json()
    assert 'rows' not in response.json()


@pytest.mark.asyncio
async def test_gen_sync_db_returns_resource_detail_not_string_body(contract_client: AsyncClient):
    response = await contract_client.get('/tool/gen/synchDb/demo_table')

    assert response.status_code == 200
    assert response.json() == {
        'info': {
            'tableId': 7,
            'tableName': 'demo_table',
            'tableComment': '演示表',
        },
        'columns': [
            {
                'columnId': 1,
                'tableId': 7,
                'columnName': 'id',
                'columnComment': '主键',
            }
        ],
        'tables': [{'tableId': 7, 'tableName': 'demo_table'}],
    }


@pytest.mark.asyncio
async def test_gen_import_table_returns_action_result(contract_client: AsyncClient):
    response = await contract_client.post('/tool/gen/importTable', params={'tables': 'demo_table,extra_table'})

    assert response.status_code == 200
    assert response.json() == {
        'tableNames': ['demo_table', 'extra_table'],
        'importedCount': 2,
    }


@pytest.mark.asyncio
async def test_gen_create_table_returns_action_result(contract_client: AsyncClient):
    response = await contract_client.post('/tool/gen/createTable', params={'sql': 'CREATE TABLE demo_table(id INT);'})

    assert response.status_code == 200
    assert response.json() == {
        'tableNames': ['demo_table'],
        'createdCount': 1,
    }


@pytest.mark.asyncio
async def test_job_create_returns_created_resource(contract_client: AsyncClient):
    response = await contract_client.post(
        '/monitor/job',
        json={
            'jobName': '演示任务',
            'jobGroup': 'DEFAULT',
            'invokeTarget': 'demo.job.run()',
            'cronExpression': '0/5 * * * * ?',
            'status': '0',
        },
    )

    assert response.status_code == 201
    assert response.headers['Location'] == 'http://testserver/monitor/job/301'
    assert response.json() == {
        'jobId': 301,
        'jobName': '演示任务',
        'jobGroup': 'DEFAULT',
        'invokeTarget': 'demo.job.run()',
        'cronExpression': '0/5 * * * * ?',
        'status': '0',
        'updateBy': 'admin',
    }


@pytest.mark.asyncio
async def test_job_change_status_returns_updated_resource(contract_client: AsyncClient):
    response = await contract_client.put('/monitor/job/changeStatus', json={'jobId': 301, 'status': '1'})

    assert response.status_code == 200
    assert response.json() == {
        'jobId': 301,
        'jobName': '演示任务',
        'jobGroup': 'DEFAULT',
        'invokeTarget': 'demo.job.run()',
        'cronExpression': '0/5 * * * * ?',
        'status': '1',
        'updateBy': 'admin',
    }


@pytest.mark.asyncio
async def test_protocol_import_returns_created_resource(contract_client: AsyncClient):
    response = await contract_client.post(
        '/system/protocol/import',
        data={'protocolName': '导入协议'},
        files={
            'file': (
                'protocol.xlsx',
                b'binary-data',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        },
    )

    assert response.status_code == 201
    assert response.headers['Location'] == 'http://testserver/system/protocol/501'
    assert response.json() == {
        'protocolId': 501,
        'protocolName': '导入协议',
        'protocolType': 'CAN',
        'status': '0',
    }
