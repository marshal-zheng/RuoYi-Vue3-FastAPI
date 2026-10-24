import json
from pathlib import Path
from types import SimpleNamespace

from scripts import export_openapi


def test_write_openapi_artifact_uses_stable_json_and_required_keys(tmp_path: Path) -> None:
    output = tmp_path / 'shared' / 'openapi.json'
    schema = {
        'paths': {'/health': {'get': {'responses': {'200': {'description': 'OK'}}}}},
        'openapi': '3.1.0',
        'info': {'title': 'Test API', 'version': '1.0.0'},
    }

    written = export_openapi.write_openapi_artifact(output, schema)

    assert output.exists()
    assert written == output.read_text(encoding='utf-8')
    parsed = json.loads(written)
    assert parsed['openapi'] == '3.1.0'
    assert parsed['paths']['/health']['get']['responses']['200']['description'] == 'OK'
    assert list(parsed.keys()) == ['info', 'openapi', 'paths']


def test_check_openapi_artifact_detects_drift(tmp_path: Path) -> None:
    output = tmp_path / 'openapi.json'
    export_openapi.write_openapi_artifact(output, {'openapi': '3.1.0', 'paths': {}})

    assert export_openapi.check_openapi_artifact(output, {'openapi': '3.1.0', 'paths': {}})
    assert not export_openapi.check_openapi_artifact(output, {'openapi': '3.1.0', 'paths': {'/new': {}}})


def test_build_openapi_schema_loads_configured_app(monkeypatch) -> None:
    fake_app = SimpleNamespace(openapi=lambda: {'openapi': '3.1.0', 'paths': {}})
    monkeypatch.setattr(export_openapi, '_load_app', lambda app_import: fake_app)

    assert export_openapi.build_openapi_schema(app_import='fake:app') == {'openapi': '3.1.0', 'paths': {}}
