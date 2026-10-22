from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

import yaml
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.database import Base
from module_admin.entity.do.db_workflow_do import DbWorkflowArtifactDO
from scripts.internal.db_workflow.finalize_release_service import finalize_release_artifacts
from scripts.internal.db_workflow.workflow_verify_service import inspect_release_workflow

if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _write_seed_data_tree(seed_data_dir: Path) -> None:
    modules_root = seed_data_dir.parents[1] / 'capabilities' / 'modules'
    _write_yaml(
        modules_root / 'platform.module.yaml',
        {
            'version': '1',
            'module_key': 'platform',
            'menus': [
                {
                    'menu_id': 1,
                    'menu_key': 'platform.system',
                    'menu_name': '系统管理',
                    'parent_id': 0,
                    'order_num': 1,
                    'path': 'system',
                    'component': None,
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'M',
                    'visible': '0',
                    'status': '0',
                    'perms': '',
                    'icon': 'system',
                    'remark': '',
                },
                {
                    'menu_id': 100,
                    'menu_key': 'platform.system.config',
                    'menu_name': '参数配置',
                    'parent_id': 1,
                    'parent_menu_key': 'platform.system',
                    'order_num': 1,
                    'path': 'config',
                    'component': 'system/config/index',
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'C',
                    'visible': '0',
                    'status': '0',
                    'perms': 'system:config:list',
                    'icon': 'setting',
                    'remark': '',
                },
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': ['platform.system.config']}],
            'dict_types': [
                {
                    'dict_id': 1,
                    'dict_name': '设备状态',
                    'dict_type': 'sys_device_status',
                    'status': '0',
                    'remark': '',
                }
            ],
            'dict_data': [
                {
                    'dict_code': 1,
                    'dict_sort': 1,
                    'dict_label': '启用',
                    'dict_value': 'enabled',
                    'dict_type': 'sys_device_status',
                    'css_class': '',
                    'list_class': 'success',
                    'is_default': 'Y',
                    'status': '0',
                    'remark': '',
                }
            ],
            'configs': [
                {
                    'config_id': 1,
                    'config_name': '设备默认超时',
                    'config_key': 'device.default.timeout',
                    'config_value': '30',
                    'config_type': 'Y',
                    'remark': '',
                }
            ],
        },
    )
    _write_yaml(
        seed_data_dir / 'base' / 'roles.yaml',
        {
            'roles': [
                {
                    'role_id': 2,
                    'role_name': '普通角色',
                    'role_key': 'common',
                    'role_sort': 2,
                    'status': '0',
                    'del_flag': '0',
                }
            ]
        },
    )
    _write_yaml(
        seed_data_dir / 'release-plan.yaml',
        {
            'version': '2',
            'release_key': '2026-04-device-config',
            'modules': {'platform': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')


def _write_entrypoints(project_root: Path, *, start_script_body: str | None = None) -> None:
    (project_root.parent / 'scripts').mkdir(parents=True, exist_ok=True)
    (project_root.parent / 'scripts' / 'start.sh').write_text(
        start_script_body
        or '\n'.join(
            (
                '#!/bin/bash',
                'python scripts/db.py status',
                'dev-sync',
                'deploy',
            )
        )
        + '\n',
        encoding='utf-8',
    )
    backend_root = project_root
    (backend_root / 'scripts').mkdir(parents=True, exist_ok=True)
    (backend_root / 'docker-entrypoint.sh').write_text(
        '\n'.join(
            (
                '#!/bin/bash',
                'python scripts/db.py deploy --revision head',
                'python scripts/db.py bootstrap-seed --env "${APP_ENV:-prod}"',
            )
        )
        + '\n',
        encoding='utf-8',
    )
    (backend_root / 'server.py').write_text(
        '\n'.join(
            (
                'def bootstrap(app):',
                '    app.state.dev_menu_sync_runtime = None',
            )
        )
        + '\n',
        encoding='utf-8',
    )


async def _create_schema(database_url: str) -> None:
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


async def _create_session_factory():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(bind=engine, expire_on_commit=False), engine


async def _record_deploy(session_factory) -> None:
    async with session_factory() as session:
        session.add(
            DbWorkflowArtifactDO(
                bundle_id='20260404_001_initial-baseline',
                artifact_type='managed-data',
                artifact_checksum='checksum',
                apply_status='success',
                applied_at=datetime(2026, 4, 4, 12, 0, 0),
                applied_by='pytest',
            )
        )
        await session.commit()


def test_inspect_release_workflow_detects_pending_finalize(tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    _write_seed_data_tree(seed_data_dir)
    _write_entrypoints(project_root)
    session_factory, engine = asyncio.run(_create_session_factory())

    try:
        inspection = inspect_release_workflow(
            project_root=project_root,
            session_factory=session_factory,
        )
    finally:
        asyncio.run(engine.dispose())

    assert inspection.declaration_validation.status == 'success'
    assert inspection.artifact_validation.status == 'success'
    assert inspection.artifact_validation.result == 'no-op'
    assert inspection.bundle_chain.status == 'success'
    assert inspection.bundle_chain.result == 'no-op'
    assert inspection.bypass_entrypoints.status == 'success'
    assert inspection.compiled_checksum
    assert inspection.release_plan_checksum
    assert inspection.managed_data_drift == 'drift'
    assert set(inspection.managed_data_details) == {
        'sys_menu:1',
        'sys_menu:100',
        'sys_role_menu:2:100',
        'sys_dict_type:1',
        'sys_dict_data:1',
        'sys_config:1',
    }
    assert inspection.visibility_drift == 'drift'
    assert inspection.pending_release_bundle == 'required'
    assert inspection.last_successful_action == 'unknown'


def test_inspect_release_workflow_reports_clean_after_bundle_finalize(tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    _write_seed_data_tree(seed_data_dir)
    _write_entrypoints(project_root)

    finalize_db = tmp_path / 'finalize.sqlite3'
    asyncio.run(_create_schema(f'sqlite+aiosqlite:///{finalize_db}'))
    finalize_release_artifacts(
        project_root=project_root,
        finalize_database_url=f'sqlite:///{finalize_db}',
        schema_revision='20260402_head',
        message='Device config release',
    )

    session_factory, engine = asyncio.run(_create_session_factory())
    asyncio.run(_record_deploy(session_factory))
    try:
        inspection = inspect_release_workflow(
            project_root=project_root,
            session_factory=session_factory,
        )
    finally:
        asyncio.run(engine.dispose())

    assert inspection.bundle_chain.status == 'success'
    assert inspection.artifact_validation.status == 'success'
    assert inspection.artifact_validation.result == 'validated'
    assert inspection.bundle_chain.result == 'replayed'
    assert inspection.bundle_chain.details
    assert inspection.compiled_checksum
    assert inspection.release_plan_checksum
    assert inspection.managed_data_drift == 'clean'
    assert inspection.managed_data_details == ()
    assert inspection.visibility_drift == 'clean'
    assert inspection.pending_release_bundle == 'none'
    assert inspection.last_successful_action == 'deploy'


def test_inspect_release_workflow_detects_bypass_entrypoint(tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    _write_seed_data_tree(seed_data_dir)
    _write_entrypoints(
        project_root,
        start_script_body='\n'.join(
            (
                '#!/bin/bash',
                'python scripts/db.py status',
                'apply_sql_updates',
                'deploy',
            )
        )
        + '\n',
    )
    session_factory, engine = asyncio.run(_create_session_factory())

    try:
        inspection = inspect_release_workflow(
            project_root=project_root,
            session_factory=session_factory,
        )
    finally:
        asyncio.run(engine.dispose())

    assert inspection.bypass_entrypoints.status == 'failed'
    assert inspection.bypass_entrypoints.result == 'bypass-detected'
    assert any('apply_sql_updates' in detail for detail in inspection.bypass_entrypoints.details)


def test_inspect_release_workflow_blocks_legacy_declarations_from_formal_chain(tmp_path: Path) -> None:
    project_root = tmp_path / 'backend'
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    _write_seed_data_tree(seed_data_dir)
    _write_entrypoints(project_root)
    _write_yaml(
        seed_data_dir / 'menus.registry.yaml',
        {
            'version': '1',
            'menus': [
                {
                    'menu_id': 999,
                    'menu_name': '旧入口',
                    'parent_id': 0,
                    'order_num': 1,
                    'path': 'legacy',
                    'component': None,
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'M',
                    'visible': '0',
                    'status': '0',
                    'perms': '',
                    'icon': 'menu',
                    'remark': '',
                }
            ],
            'role_grants': [],
        },
    )
    session_factory, engine = asyncio.run(_create_session_factory())

    try:
        inspection = inspect_release_workflow(
            project_root=project_root,
            session_factory=session_factory,
        )
    finally:
        asyncio.run(engine.dispose())

    assert inspection.declaration_validation.status == 'failed'
    assert inspection.declaration_validation.result == 'invalid'
    assert 'legacy declaration file is no longer supported' in (inspection.declaration_validation.error or '')
    assert inspection.artifact_validation.status == 'skipped'
    assert inspection.bundle_chain.status == 'skipped'
    assert inspection.managed_data_drift == 'invalid'
    assert inspection.visibility_drift == 'invalid'
