from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config.env import AppConfig, DevMenuSyncConfig
from config.get_db import get_db
from exceptions.exception import PermissionException, SystemException
from module_admin.entity.vo.user_vo import CurrentUserModel
from modules.identity.ports import get_current_user
from modules.system.runtime import DevMenuReconcileService, DevMenuSignatureService
from utils.log_util import logger
from utils.response_util import ResponseUtil

devMenuSyncController = APIRouter(prefix='/dev/menu', dependencies=[Depends(get_current_user)])  # noqa: N816


class DevMenuSyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dry_run: bool = Field(default=False, alias='dryRun')
    trigger: str = Field(default='manual')


def _ensure_dev_menu_api_available() -> None:
    if AppConfig.app_env != 'dev':
        if DevMenuSyncConfig.dev_menu_sync:
            logger.warning(
                'DEV_MENU_SYNC=true ignored in non-dev environment (APP_ENV={})',
                AppConfig.app_env,
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')

    if not DevMenuSyncConfig.dev_menu_sync:
        logger.warning('Dev menu API rejected because DEV_MENU_SYNC is disabled')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')


def _is_admin_user(current_user: CurrentUserModel) -> bool:
    user = current_user.user
    if user is not None and user.admin:
        return True
    if '*:*:*' in current_user.permissions:
        return True
    return 'admin' in current_user.roles


def _require_user_id(current_user: CurrentUserModel) -> int:
    if current_user.user is None or current_user.user.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    return int(current_user.user.user_id)


def _sync_state_status(sync_state: Any) -> str:
    if sync_state is None or sync_state.last_sync_success is None:
        return 'idle'
    return 'ok' if sync_state.last_sync_success else 'failed'


@devMenuSyncController.get('/signature')
async def get_dev_menu_signature(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()

    service = DevMenuSignatureService(query_db=query_db)
    signature = await service.get_user_signature(_require_user_id(current_user))

    runtime = getattr(request.app.state, 'dev_menu_sync_runtime', None)
    sync_state = runtime.state if runtime is not None else None
    synced_at = sync_state.last_sync_at.isoformat() if sync_state and sync_state.last_sync_at else None
    return ResponseUtil.success(
        data={
            'signature': signature,
            'syncedAt': synced_at,
            'lastSyncStatus': _sync_state_status(sync_state),
        }
    )


@devMenuSyncController.post('/sync')
async def post_dev_menu_sync(
    request: Request,
    payload: DevMenuSyncRequest | None = Body(default=None),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()
    if not _is_admin_user(current_user):
        raise PermissionException(user_message='仅管理员可执行开发态菜单同步')

    request_model = payload or DevMenuSyncRequest()
    trigger = (request_model.trigger or 'manual').strip() or 'manual'
    service = DevMenuReconcileService(query_db=query_db)
    report = await service.sync_once(trigger=trigger, dry_run=request_model.dry_run)

    if not request_model.dry_run:
        runtime = getattr(request.app.state, 'dev_menu_sync_runtime', None)
        if runtime is not None:
            runtime.state.last_sync_success = report.success
            runtime.state.last_sync_at = report.synced_at
            runtime.state.last_trigger = report.trigger
            runtime.state.last_error = report.error

    if not report.success:
        raise SystemException(user_message='开发态菜单同步失败', developer_message=report.error or 'unknown error')

    logger.info(
        'Manual dev menu sync finished: dry_run={}, added={}, updated={}, deleted={}, role_menu_deleted={}',
        request_model.dry_run,
        report.added,
        report.updated,
        report.deleted,
        report.role_menu_deleted,
    )
    return ResponseUtil.success(
        data={
            'trigger': report.trigger,
            'dryRun': report.dry_run,
            'success': report.success,
            'added': report.added,
            'updated': report.updated,
            'deleted': report.deleted,
            'roleMenuDeleted': report.role_menu_deleted,
            'durationMs': report.duration_ms,
            'syncedAt': report.synced_at.isoformat() if report.synced_at else None,
        }
    )
