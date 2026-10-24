#!/usr/bin/env python3
"""Export the FastAPI OpenAPI schema as a deterministic repository artifact."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from fastapi.encoders import jsonable_encoder


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DEFAULT_OUTPUT = REPO_ROOT / 'shared' / 'openapi.json'
DEFAULT_APP_IMPORT = 'server:app'


def _ensure_backend_import_path() -> None:
    backend_root = str(BACKEND_ROOT)
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)


def _load_app(app_import: str):
    _ensure_backend_import_path()
    module_name, separator, attr_path = app_import.partition(':')
    if not separator or not module_name or not attr_path:
        raise ValueError('app import must use the form "module:attribute", for example "server:app"')

    target: Any = importlib.import_module(module_name)
    for attr in attr_path.split('.'):
        target = getattr(target, attr)
    return target


def _stable_json_text(schema: dict[str, Any]) -> str:
    normalized_schema = jsonable_encoder(schema)
    return json.dumps(
        normalized_schema,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        separators=(',', ': '),
    ) + '\n'


def build_openapi_schema(app_import: str = DEFAULT_APP_IMPORT) -> dict[str, Any]:
    app = _load_app(app_import)
    schema = app.openapi()
    if not isinstance(schema, dict):
        raise TypeError(f'Expected app.openapi() to return dict, got {type(schema).__name__}')
    return schema


def write_openapi_artifact(output: Path, schema: dict[str, Any]) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    text = _stable_json_text(schema)
    output.write_text(text, encoding='utf-8')
    return text


def check_openapi_artifact(output: Path, schema: dict[str, Any]) -> bool:
    expected_text = _stable_json_text(schema)
    if not output.exists():
        print(f'OpenAPI artifact missing: {output}', file=sys.stderr)
        return False

    actual_text = output.read_text(encoding='utf-8')
    if actual_text != expected_text:
        print(
            'OpenAPI artifact drift detected. Run: '
            f'cd {BACKEND_ROOT} && python scripts/export_openapi.py --output {output}',
            file=sys.stderr,
        )
        return False
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export or check the repository OpenAPI artifact.')
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f'OpenAPI artifact output path. Defaults to {DEFAULT_OUTPUT}',
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Compare the current FastAPI schema with the artifact without writing it.',
    )
    parser.add_argument(
        '--app',
        default=DEFAULT_APP_IMPORT,
        help=f'FastAPI app import target. Defaults to {DEFAULT_APP_IMPORT}',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output.resolve()
    schema = build_openapi_schema(app_import=args.app)

    if args.check:
        if check_openapi_artifact(output, schema):
            print(f'OpenAPI artifact is up to date: {output}')
            return 0
        return 1

    write_openapi_artifact(output, schema)
    print(f'OpenAPI artifact exported: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
