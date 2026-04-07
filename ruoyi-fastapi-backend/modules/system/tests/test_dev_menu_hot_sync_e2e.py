from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.database import Base
from module_admin.entity.do.menu_do import MenuDO
from module_admin.entity.do.role_do import RoleDO, RoleMenuDO
from module_admin.entity.do.user_do import UserDO, UserRoleDO
from modules.system.runtime.dev_menu_event_broker import DevMenuEventBroker
from modules.system.runtime.dev_menu_signature_service import DevMenuSignatureService
from scripts.internal.db_workflow.managed_data_declaration_loader import ManagedDataDeclarationLoader
from scripts.internal.db_workflow.managed_data_fast_reconcile_service import ManagedDataFastReconcileService


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding='utf-8')


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _write_module_tree(
    project_root: Path,
    *,
    leaf_menu_id: int,
    leaf_menu_key: str,
    leaf_menu_name: str,
    leaf_component: str,
    configs: list[dict] | None = None,
) -> Path:
    seed_data_dir = project_root / 'scripts' / 'seed_data'
    modules_root = project_root / 'capabilities' / 'modules'
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
                    'menu_id': leaf_menu_id,
                    'menu_key': leaf_menu_key,
                    'menu_name': leaf_menu_name,
                    'parent_id': 1,
                    'parent_menu_key': 'platform.system',
                    'order_num': 1,
                    'path': f'menu-{leaf_menu_id}',
                    'component': leaf_component,
                    'query': None,
                    'route_name': '',
                    'is_frame': 1,
                    'is_cache': 0,
                    'menu_type': 'C',
                    'visible': '0',
                    'status': '0',
                    'perms': f'system:menu:{leaf_menu_id}',
                    'icon': 'menu',
                    'remark': '',
                },
            ],
            'role_grants': [{'role_key': 'common', 'menu_keys': [leaf_menu_key]}],
            'dict_types': [],
            'dict_data': [],
            'configs': list(configs or []),
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
            'release_key': '2026-04-platform',
            'modules': {'platform': True},
        },
    )
    _write_text(seed_data_dir / 'menus.registry.yaml', 'version: "1"\nmenus: []\nrole_grants: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_types.yaml', 'dict_types: []\n')
    _write_text(seed_data_dir / 'base' / 'dict_data.yaml', 'dict_data: []\n')
    _write_text(seed_data_dir / 'base' / 'configs.yaml', 'configs: []\n')
    return seed_data_dir


@pytest.fixture
async def reconcile_context(tmp_path: Path):
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        echo=False,
        poolclass=StaticPool,
        connect_args={'check_same_thread': False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)
    async with session_factory() as session, session.begin():
        session.add(
            UserDO(
                user_id=8200,
                user_name='dev-e2e',
                nick_name='dev-e2e',
                password='test',
                status='0',
                del_flag='0',
            )
        )
        session.add(
            RoleDO(
                role_id=2,
                role_name='普通角色',
                role_key='common',
                role_sort=2,
                status='0',
                del_flag='0',
            )
        )
        session.add(UserRoleDO(user_id=8200, role_id=2))

    yield tmp_path, session_factory

    await engine.dispose()


async def _user_signature(session_factory, user_id: int) -> str:
    async with session_factory() as session:
        return await DevMenuSignatureService(query_db=session).get_user_signature(user_id)


async def _menu_snapshot(session_factory) -> tuple[set[int], set[tuple[int, int]]]:
    async with session_factory() as session:
        menu_ids = {int(row.menu_id) for row in (await session.execute(select(MenuDO.menu_id))).all()}
        role_menu_pairs = {
            (int(row.role_id), int(row.menu_id))
            for row in (await session.execute(select(RoleMenuDO.role_id, RoleMenuDO.menu_id))).all()
        }
    return menu_ids, role_menu_pairs


def _loader_factory(seed_data_dir: Path):
    return lambda: ManagedDataDeclarationLoader(seed_data_dir=seed_data_dir)


def _publish_if_menu_reload_required(broker: DevMenuEventBroker, report) -> int | None:
    if not report.menu_reload_required:
        return None
    return broker.publish_menu_changed(
        trigger=report.trigger,
        compiled_checksum=report.compiled_checksum,
        synced_at=report.synced_at,
    )


@pytest.mark.asyncio
async def test_capability_module_hot_reconcile_updates_signature_and_sse_event(reconcile_context) -> None:
    project_root, session_factory = reconcile_context
    seed_data_dir = _write_module_tree(
        project_root,
        leaf_menu_id=100,
        leaf_menu_key='platform.system.config',
        leaf_menu_name='参数配置',
        leaf_component='system/config/index',
    )
    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=_loader_factory(seed_data_dir),
    )
    broker = DevMenuEventBroker(heartbeat_seconds=60, replay_buffer_size=1)

    first_report = await service.reconcile(trigger='startup')
    assert first_report.success is True
    assert first_report.state_changed is True
    assert first_report.menu_reload_required is True
    first_event_id = _publish_if_menu_reload_required(broker, first_report)

    signature_before = await _user_signature(session_factory, 8200)

    _write_module_tree(
        project_root,
        leaf_menu_id=101,
        leaf_menu_key='platform.system.audit',
        leaf_menu_name='审计日志',
        leaf_component='monitor/audit/index',
    )
    second_report = await service.reconcile(
        trigger='file_change',
        previous_compiled_checksum=first_report.compiled_checksum,
    )
    assert second_report.success is True
    assert second_report.state_changed is True
    assert second_report.menu_reload_required is True
    second_event_id = _publish_if_menu_reload_required(broker, second_report)

    signature_after = await _user_signature(session_factory, 8200)
    menu_ids, role_menu_pairs = await _menu_snapshot(session_factory)

    assert 100 not in menu_ids
    assert 101 in menu_ids
    assert (2, 100) not in role_menu_pairs
    assert (2, 101) in role_menu_pairs
    assert signature_before != signature_after

    stream = broker.subscribe(user_id=8200, last_event_id=first_event_id)
    ready_event = await anext(stream)
    replay_event = await anext(stream)

    assert ready_event.event == 'ready'
    assert replay_event.event == 'menu_changed'
    assert replay_event.event_id == second_event_id
    assert replay_event.data['trigger'] == 'file_change'
    assert replay_event.data['compiledChecksum'] == second_report.compiled_checksum

    await stream.aclose()
    await broker.close()


@pytest.mark.asyncio
async def test_capability_module_hot_reconcile_noop_keeps_sse_sequence_stable(reconcile_context) -> None:
    project_root, session_factory = reconcile_context
    seed_data_dir = _write_module_tree(
        project_root,
        leaf_menu_id=100,
        leaf_menu_key='platform.system.config',
        leaf_menu_name='参数配置',
        leaf_component='system/config/index',
    )
    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=_loader_factory(seed_data_dir),
    )
    broker = DevMenuEventBroker(heartbeat_seconds=60, replay_buffer_size=1)

    first_report = await service.reconcile(trigger='startup')
    assert first_report.success is True
    assert first_report.state_changed is True
    assert first_report.menu_reload_required is True
    initial_event_id = _publish_if_menu_reload_required(broker, first_report)

    second_report = await service.reconcile(
        trigger='file_change',
        previous_compiled_checksum=first_report.compiled_checksum,
    )

    assert second_report.success is True
    assert second_report.state_changed is False
    assert second_report.menu_reload_required is False
    assert second_report.skipped_reason == 'compiled_checksum_unchanged'
    assert broker.last_event_id == initial_event_id

    await broker.close()


@pytest.mark.asyncio
async def test_capability_module_config_only_reconcile_keeps_signature_and_sse_sequence_stable(reconcile_context) -> None:
    project_root, session_factory = reconcile_context
    seed_data_dir = _write_module_tree(
        project_root,
        leaf_menu_id=100,
        leaf_menu_key='platform.system.config',
        leaf_menu_name='参数配置',
        leaf_component='system/config/index',
    )
    service = ManagedDataFastReconcileService(
        session_factory=session_factory,
        declaration_loader_factory=_loader_factory(seed_data_dir),
    )
    broker = DevMenuEventBroker(heartbeat_seconds=60, replay_buffer_size=1)

    first_report = await service.reconcile(trigger='startup')
    first_event_id = _publish_if_menu_reload_required(broker, first_report)
    assert first_event_id == 1

    signature_before = await _user_signature(session_factory, 8200)
    _write_module_tree(
        project_root,
        leaf_menu_id=100,
        leaf_menu_key='platform.system.config',
        leaf_menu_name='参数配置',
        leaf_component='system/config/index',
        configs=[
            {
                'config_id': 300,
                'config_name': '设备默认超时',
                'config_key': 'device.default.timeout',
                'config_value': '45',
                'config_type': 'Y',
                'remark': '',
            }
        ],
    )

    second_report = await service.reconcile(
        trigger='file_change',
        previous_compiled_checksum=first_report.compiled_checksum,
    )
    signature_after = await _user_signature(session_factory, 8200)

    assert second_report.success is True
    assert second_report.state_changed is True
    assert second_report.changed_domains == ('configs',)
    assert second_report.menu_reload_required is False
    assert _publish_if_menu_reload_required(broker, second_report) is None
    assert signature_after == signature_before
    assert broker.last_event_id == first_event_id

    await broker.close()
