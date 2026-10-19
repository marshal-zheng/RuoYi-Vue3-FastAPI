"""Deterministic-resource CRUD; no caller-controlled owner or unconditional overwrite."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.get_db import get_db
from container.dependencies import service_provider
from module_admin.entity.vo.dashboard_vo import DashboardSaveModel, DashboardScope
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.project.application.services.project_service import ProjectService
from modules.system.application.services.dashboard_service import DashboardService
from modules.system.infrastructure.dashboard_repository import DashboardRepository, DashboardRevisionConflictError
from utils.response_util import ResponseUtil

dashboard_controller = APIRouter(prefix='/system/dashboard', dependencies=[Depends(get_current_user)])


def dashboard_service(
    db: AsyncSession = Depends(get_db),
    project: ProjectService = Depends(service_provider('project_service')),
):
    return DashboardService(DashboardRepository(db), project.get_project_detail)


async def conflict_response(request, service, scope, key, user):
    remote = await service.load(scope, key, user)
    return ResponseUtil.problem_details(
        request=request,
        http_status=409,
        title='仪表盘已被其他操作修改',
        type_slug='dashboard-revision-conflict',
        error_code='dashboard_revision_conflict',
        errors=[{'field': 'expectedRevision', 'code': 'conflict', 'remote': remote}],
    )


@dashboard_controller.get('/{scope}/{key}')
async def load_dashboard(
    scope: DashboardScope,
    key: str,
    user: CurrentUserModel = Depends(get_current_user),
    service: DashboardService = Depends(dashboard_service),
):
    return ResponseUtil.ok_resource(await service.load(scope, key, user))


@dashboard_controller.put('/{scope}/{key}')
async def save_dashboard(
    request: Request,
    scope: DashboardScope,
    key: str,
    body: DashboardSaveModel,
    user: CurrentUserModel = Depends(get_current_user),
    service: DashboardService = Depends(dashboard_service),
):
    try:
        return ResponseUtil.ok_resource(await service.save(scope, key, user, body))
    except DashboardRevisionConflictError:
        return await conflict_response(request, service, scope, key, user)


@dashboard_controller.delete('/{scope}/{key}')
async def remove_dashboard(
    request: Request,
    scope: DashboardScope,
    key: str,
    expected_revision: int = Query(alias='expectedRevision', ge=1),
    user: CurrentUserModel = Depends(get_current_user),
    service: DashboardService = Depends(dashboard_service),
):
    try:
        await service.remove(scope, key, user, expected_revision)
        return ResponseUtil.no_content()
    except DashboardRevisionConflictError:
        return await conflict_response(request, service, scope, key, user)
