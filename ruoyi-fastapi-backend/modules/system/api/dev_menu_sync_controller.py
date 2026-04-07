from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from module_admin.entity.vo.user_vo import CurrentUserModel

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from config.env import AppConfig, DataBaseWorkflowConfig, DevManagedDataHotReconcileConfig
from config.get_db import get_db
from exceptions.exception import PermissionException, SystemException
from modules.identity.ports import get_current_user
from modules.system.application.services.capability_gate_service import invalidate_capability_gate_service
from modules.system.runtime import (
    DevMenuEventBroker,
    DevMenuSignatureService,
    is_dev_managed_data_hot_reconcile_enabled,
)
from scripts.internal.db_workflow.managed_data_fast_reconcile_service import ManagedDataFastReconcileService
from utils.log_util import logger
from utils.response_util import ResponseUtil

devMenuSyncController = APIRouter(prefix='/dev/menu', dependencies=[Depends(get_current_user)])  # noqa: N816


class DevMenuSyncRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dry_run: bool = Field(default=False, alias='dryRun')
    trigger: str = Field(default='manual')


def _ensure_dev_menu_api_available() -> None:
    if not is_dev_managed_data_hot_reconcile_enabled():
        logger.debug(
            'Dev menu API unavailable (APP_ENV={}, DB_WORKFLOW_MODE={}, enabled={})',
            AppConfig.app_env,
            DataBaseWorkflowConfig.db_workflow_mode,
            DevManagedDataHotReconcileConfig.dev_managed_data_hot_reconcile_enabled,
        )
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


def _sync_state_payload(sync_state: Any) -> dict[str, Any]:
    if sync_state is None:
        return {
            'lastSeenSnapshotChecksum': None,
            'lastAppliedSnapshotChecksum': None,
            'lastAppliedCompiledChecksum': None,
            'pendingSnapshotChecksum': None,
            'retryCount': 0,
            'nextRetryAt': None,
            'lastSyncSuccess': None,
            'lastSyncAt': None,
            'lastTrigger': None,
            'lastError': None,
            'lastEventId': 0,
        }
    return sync_state.as_dict()


def _runtime_manifest_health(runtime: Any) -> tuple[bool, int]:
    if runtime is None:
        return False, 0
    modules_root = getattr(runtime, 'modules_root', None)
    if modules_root is None:
        return False, 0
    if not modules_root.exists() or not modules_root.is_dir():
        return False, 0
    return True, sum(1 for _ in modules_root.glob('*.module.yaml'))


def _get_dev_menu_runtime(request: Request) -> Any:
    return getattr(request.app.state, 'dev_menu_sync_runtime', None) or getattr(
        request.app.state,
        'dev_managed_data_hot_reconcile_runtime',
        None,
    )


def _get_dev_menu_event_broker(request: Request) -> DevMenuEventBroker | None:
    return getattr(request.app.state, 'dev_menu_event_broker', None) or getattr(
        request.app.state,
        'dev_managed_data_hot_reconcile_event_broker',
        None,
    )


def _require_dev_menu_event_broker(request: Request) -> DevMenuEventBroker:
    broker = _get_dev_menu_event_broker(request)
    if broker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not Found')
    return broker


def _parse_last_event_id(request: Request) -> int | None:
    raw_value = request.headers.get('last-event-id')
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except ValueError:
        return None


@devMenuSyncController.get('/signature')
async def get_dev_menu_signature(
    request: Request,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()

    service = DevMenuSignatureService(query_db=query_db)
    signature = await service.get_user_signature(_require_user_id(current_user))

    runtime = _get_dev_menu_runtime(request)
    sync_state = runtime.state if runtime is not None else None
    synced_at = sync_state.last_sync_at.isoformat() if sync_state and sync_state.last_sync_at else None
    return ResponseUtil.success(
        data={
            'signature': signature,
            'syncedAt': synced_at,
            'lastSyncStatus': _sync_state_status(sync_state),
        }
    )


@devMenuSyncController.get('/status')
async def get_dev_menu_status(
    request: Request,
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()
    runtime = _get_dev_menu_runtime(request)
    sync_state = runtime.state if runtime is not None else None
    modules_root_exists, manifest_count = _runtime_manifest_health(runtime)
    return ResponseUtil.success(
        data={
            'enabled': True,
            'modulesRoot': str(runtime.modules_root) if runtime is not None else None,
            'modulesRootExists': modules_root_exists,
            'manifestCount': manifest_count,
            'watchIntervalMs': DevManagedDataHotReconcileConfig.dev_managed_data_watch_interval_ms,
            'debounceMs': DevManagedDataHotReconcileConfig.dev_managed_data_debounce_ms,
            'retryBackoffMs': DevManagedDataHotReconcileConfig.dev_managed_data_retry_backoff_ms,
            'retryMaxBackoffMs': DevManagedDataHotReconcileConfig.dev_managed_data_retry_max_backoff_ms,
            'lastSyncStatus': _sync_state_status(sync_state),
            **_sync_state_payload(sync_state),
        }
    )


@devMenuSyncController.get('/events')
async def get_dev_menu_events(
    request: Request,
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()
    broker = _require_dev_menu_event_broker(request)
    return ResponseUtil.streaming(
        data=broker.stream(
            user_id=_require_user_id(current_user),
            last_event_id=_parse_last_event_id(request),
        ),
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
        media_type='text/event-stream',
    )


@devMenuSyncController.post('/sync')
async def post_dev_menu_sync(
    request: Request,
    payload: DevMenuSyncRequest | None = Body(default=None),
    current_user: CurrentUserModel = Depends(get_current_user),
):
    _ensure_dev_menu_api_available()
    if not _is_admin_user(current_user):
        raise PermissionException(user_message='仅管理员可执行开发态菜单同步')

    request_model = payload or DevMenuSyncRequest()
    trigger = (request_model.trigger or 'manual').strip() or 'manual'
    runtime = _get_dev_menu_runtime(request)
    broker = _get_dev_menu_event_broker(request)
    service = ManagedDataFastReconcileService(redis_client=getattr(request.app.state, 'redis', None))

    async def _run_reconcile():
        return await service.reconcile(
            trigger=trigger,
            dry_run=request_model.dry_run,
            previous_compiled_checksum=(
                None
                if request_model.dry_run or runtime is None
                else runtime.state.last_applied_compiled_checksum
            ),
        )

    report = await runtime.run_serialized(_run_reconcile) if runtime is not None else await _run_reconcile()

    event_id = None
    if report.success and not request_model.dry_run and report.skipped_reason != 'compiled_checksum_unchanged':
        invalidate_capability_gate_service(request.app)
    if report.success and not request_model.dry_run and report.menu_reload_required and broker is not None:
        event_id = broker.publish_menu_changed(
            trigger=report.trigger,
            compiled_checksum=report.compiled_checksum or None,
            synced_at=report.synced_at,
        )

    if runtime is not None and not request_model.dry_run:
        if report.success:
            runtime.record_sync_success(
                trigger=report.trigger,
                compiled_checksum=report.compiled_checksum or None,
                synced_at=report.synced_at,
                event_id=event_id,
            )
        else:
            runtime.record_sync_failure(
                trigger=report.trigger,
                error=report.error or 'unknown error',
                synced_at=report.synced_at,
            )

    if not report.success:
        logger.error(
            'Manual dev managed-data sync failed: dry_run={}, trigger={}, duration_ms={}, error={}',
            request_model.dry_run,
            report.trigger,
            report.duration_ms,
            report.error,
        )
        raise SystemException(user_message='开发态菜单同步失败', developer_message=report.error or 'unknown error')

    logger.info(
        'Manual dev managed-data sync finished: dry_run={}, state_changed={}, menu_reload_required={}, '
        'changed_domains={}, applied_operations={}, skipped_reason={}',
        request_model.dry_run,
        report.state_changed,
        report.menu_reload_required,
        report.changed_domains,
        report.applied_operations,
        report.skipped_reason,
    )
    return ResponseUtil.success(
        data={
            'trigger': report.trigger,
            'dryRun': report.dry_run,
            'success': report.success,
            'compiledChecksum': report.compiled_checksum or None,
            'affectedObjects': list(report.affected_objects),
            'affectedObjectsCount': len(report.affected_objects),
            'residualObjects': list(report.residual_objects),
            'appliedOperations': report.applied_operations,
            'skippedOperations': report.skipped_operations,
            'metadataUpdatedObjects': report.metadata_updated_objects,
            'metadataDeactivatedObjects': report.metadata_deactivated_objects,
            'changedDomains': list(report.changed_domains),
            'menuReloadRequired': report.menu_reload_required,
            'postconditionStatus': report.postcondition_status,
            'stateChanged': report.state_changed,
            'skippedReason': report.skipped_reason,
            'durationMs': report.duration_ms,
            'syncedAt': report.synced_at.isoformat() if report.synced_at else None,
        }
    )
