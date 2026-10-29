#!/usr/bin/env python3
# ruff: noqa: E402, PLC0415 - CLI imports run after the environment is selected
"""File asset operations entrypoint (storage bootstrap/check, deletion retry, sweeps, consistency).

Examples:
    python scripts/file_assets.py --env dev print-app-policy
    python scripts/file_assets.py --env dev bootstrap-storage
    python scripts/file_assets.py --env dev check-storage --write-probe
    python scripts/file_assets.py --env dev retry-deletes [--asset-id ID ...]
    python scripts/file_assets.py --env dev check-consistency [--prefix assets/2026/10/]
    python scripts/file_assets.py --env dev sweep-orphans --prefix assets/2026/08/ [--apply] [--include-unowned]

Admin credentials for bootstrap are read only from FILE_ASSET_S3_ADMIN_ACCESS_KEY/SECRET_KEY and are never
used by the web process. Every `--apply` first requires a confirmed bucket ownership marker.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from config.env import FileAssetConfig


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _require_configured() -> None:
    missing = FileAssetConfig.missing_settings
    if missing:
        raise SystemExit(f'file assets are not configured; missing: {", ".join(missing)}')


async def _services(*, check_ownership: bool = True):
    import container  # noqa: F401 - registers owner policies
    from config.database import AsyncSessionLocal
    from modules.file_assets.application.composition import configure_file_assets

    services = configure_file_assets(AsyncSessionLocal)
    if check_ownership:
        await services.runtime.ownership.startup()
        await services.runtime.ownership.stop()
    return services


def cmd_print_app_policy(_args) -> int:
    from modules.file_assets.infrastructure.bootstrap import app_policy

    bucket = FileAssetConfig.file_asset_s3_bucket or '<bucket>'
    _print(app_policy(bucket))
    return 0


def cmd_bootstrap_storage(args) -> int:
    from modules.file_assets.infrastructure.bootstrap import bootstrap_storage

    settings = FileAssetConfig
    admin_key = os.environ.get('FILE_ASSET_S3_ADMIN_ACCESS_KEY', '')
    admin_secret = os.environ.get('FILE_ASSET_S3_ADMIN_SECRET_KEY', '')
    if not (settings.file_asset_s3_endpoint and settings.file_asset_s3_bucket and settings.file_asset_installation_id):
        raise SystemExit('FILE_ASSET_S3_ENDPOINT, FILE_ASSET_S3_BUCKET and FILE_ASSET_INSTALLATION_ID are required')
    if not (admin_key and admin_secret):
        raise SystemExit('FILE_ASSET_S3_ADMIN_ACCESS_KEY / FILE_ASSET_S3_ADMIN_SECRET_KEY are required for bootstrap')
    report = bootstrap_storage(
        endpoint=settings.file_asset_s3_endpoint,
        region=settings.file_asset_s3_region,
        addressing_style=settings.file_asset_s3_addressing_style,
        bucket=settings.file_asset_s3_bucket,
        installation_id=settings.file_asset_installation_id,
        admin_access_key=admin_key,
        admin_secret_key=admin_secret,
        take_over=args.take_over,
        confirm_installation=args.confirm_installation,
    )
    _print(report.__dict__)
    return 0 if report.ok else 1


def cmd_check_storage(args) -> int:
    from modules.file_assets.infrastructure.bootstrap import check_app_access

    _require_configured()
    settings = FileAssetConfig
    report = check_app_access(
        endpoint=settings.file_asset_s3_endpoint,
        region=settings.file_asset_s3_region,
        addressing_style=settings.file_asset_s3_addressing_style,
        bucket=settings.file_asset_s3_bucket,
        installation_id=settings.file_asset_installation_id,
        access_key=settings.file_asset_s3_access_key.get_secret_value(),
        secret_key=settings.file_asset_s3_secret_key.get_secret_value(),
        write_probe=args.write_probe,
    )
    _print(report.__dict__)
    return 0 if report.ok else 1


async def _retry_deletes(args) -> int:
    services = await _services(check_ownership=False)
    count = await services.cleanup.retry_deletes(args.asset_id or None)
    _print({'rescheduled': count})
    return 0


async def _check_consistency(args) -> int:
    _require_configured()
    services = await _services()
    _print(await services.cleanup.check_consistency(args.prefix))
    return 0


async def _sweep_orphans(args) -> int:
    _require_configured()
    if not args.prefix.startswith('assets/'):
        raise SystemExit('--prefix must name an assets/ month prefix, e.g. assets/2026/08/')
    services = await _services()
    report = await services.cleanup.sweep_orphans(
        [args.prefix], apply=args.apply, include_unowned=args.include_unowned, use_cursor=False
    )
    _print(report.to_dict())
    return 0 if report.skipped_reason is None else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='File asset operations')
    parser.add_argument('--env', default='', help='环境（加载 .env.<env> 与 .env.<env>.local）')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('print-app-policy', help='输出应用账户最小权限策略 JSON').set_defaults(
        func=cmd_print_app_policy
    )
    bootstrap = commands.add_parser('bootstrap-storage', help='用管理员凭据建私有桶、核对设置并写安装标识')
    bootstrap.add_argument('--take-over', action='store_true', help='环境转交：改写不一致的安装标识')
    bootstrap.add_argument('--confirm-installation', help='--take-over 时必须给出桶内现有的安装标识')
    bootstrap.set_defaults(func=cmd_bootstrap_storage)
    check = commands.add_parser('check-storage', help='用应用凭据核对桶访问、安装标识与最小权限')
    check.add_argument('--write-probe', action='store_true', help='写入/读取/删除一个探针对象并验证越权写被拒绝')
    check.set_defaults(func=cmd_check_storage)
    retry = commands.add_parser('retry-deletes', help='立即重试删除失败中的资产（不缩短宽限期）')
    retry.add_argument('--asset-id', action='append', help='只重试指定资产，可重复')
    retry.set_defaults(func=lambda a: asyncio.run(_retry_deletes(a)))
    consistency = commands.add_parser('check-consistency', help='只报告：孤儿、无主、格式外键与 READY 缺失对象')
    consistency.add_argument('--prefix', help='只核对该前缀，默认全桶（跳过 _meta/）')
    consistency.set_defaults(func=lambda a: asyncio.run(_check_consistency(a)))
    sweep = commands.add_parser('sweep-orphans', help='按指定月份前缀执行与定时任务相同的孤儿判定（默认 dry-run）')
    sweep.add_argument('--prefix', required=True, help='例如 assets/2026/08/')
    sweep.add_argument('--apply', action='store_true', help='实际删除（要求存储归属已确认）')
    sweep.add_argument('--include-unowned', action='store_true', help='同时删除无资产记录的对象（需 --apply）')
    sweep.set_defaults(func=lambda a: asyncio.run(_sweep_orphans(a)))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, 'include_unowned', False) and not args.apply:
        raise SystemExit('--include-unowned requires --apply')
    return int(args.func(args) or 0)


if __name__ == '__main__':
    raise SystemExit(main())
