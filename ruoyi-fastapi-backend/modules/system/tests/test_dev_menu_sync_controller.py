from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exceptions.handle import handle_exception
from module_admin.entity.vo.user_vo import CurrentUserModel, UserInfoModel
from modules.system.runtime import SyncReport


def _build_admin_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['*:*:*'],
        roles=['admin'],
        user=UserInfoModel(
            userId=1,
            userName='admin',
            nickName='admin',
        ),
    )


def _build_non_admin_user() -> CurrentUserModel:
    return CurrentUserModel(
        permissions=['system:menu:list'],
        roles=['common'],
        user=UserInfoModel(
            userId=2,
            userName='common',
            nickName='common',
        ),
    )


@pytest.fixture
def controller_context():
    from modules.system.api import dev_menu_sync_controller as controller_module

    app = FastAPI()
    handle_exception(app)
    app.state.dev_menu_sync_runtime = None
    app.include_router(controller_module.devMenuSyncController)

    async def override_get_current_user() -> CurrentUserModel:
        return _build_admin_user()

    async def override_get_db():
        yield None

    app.dependency_overrides[controller_module.get_current_user] = override_get_current_user
    app.dependency_overrides[controller_module.get_db] = override_get_db

    with TestClient(app) as client:
        yield client, app, controller_module


def test_signature_endpoint_returns_signature_when_enabled(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DevMenuSyncConfig, 'dev_menu_sync', True, raising=False)
    get_signature = AsyncMock(return_value='signature-demo')
    monkeypatch.setattr(controller_module.DevMenuSignatureService, 'get_user_signature', get_signature)

    response = client.get('/dev/menu/signature')
    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['signature'] == 'signature-demo'
    assert payload['lastSyncStatus'] in {'idle', 'ok', 'failed'}
    get_signature.assert_awaited()


def test_signature_endpoint_returns_404_when_unavailable(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'prod', raising=False)
    monkeypatch.setattr(controller_module.DevMenuSyncConfig, 'dev_menu_sync', True, raising=False)

    response = client.get('/dev/menu/signature')
    assert response.status_code == 404


def test_signature_endpoint_returns_404_when_switch_disabled(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DevMenuSyncConfig, 'dev_menu_sync', False, raising=False)

    response = client.get('/dev/menu/signature')
    assert response.status_code == 404


def test_sync_endpoint_requires_admin(controller_context, monkeypatch):
    client, app, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DevMenuSyncConfig, 'dev_menu_sync', True, raising=False)

    async def override_get_current_user() -> CurrentUserModel:
        return _build_non_admin_user()

    app.dependency_overrides[controller_module.get_current_user] = override_get_current_user
    response = client.post('/dev/menu/sync', json={'dryRun': True})
    assert response.status_code == 403


def test_sync_endpoint_supports_dry_run(controller_context, monkeypatch):
    client, _, controller_module = controller_context

    monkeypatch.setattr(controller_module.AppConfig, 'app_env', 'dev', raising=False)
    monkeypatch.setattr(controller_module.DevMenuSyncConfig, 'dev_menu_sync', True, raising=False)
    sync_once = AsyncMock(
        return_value=SyncReport(
            success=True,
            trigger='manual',
            added=1,
            updated=2,
            deleted=3,
            role_menu_deleted=4,
            duration_ms=12,
            dry_run=True,
            synced_at=datetime(2026, 2, 27, 10, 0, 0),
        )
    )
    monkeypatch.setattr(controller_module.DevMenuReconcileService, 'sync_once', sync_once)

    response = client.post('/dev/menu/sync', json={'dryRun': True, 'trigger': 'manual'})
    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['dryRun'] is True
    assert payload['added'] == 1
    assert payload['updated'] == 2
    assert payload['deleted'] == 3
    assert payload['roleMenuDeleted'] == 4
    sync_once.assert_awaited_once_with(trigger='manual', dry_run=True)
