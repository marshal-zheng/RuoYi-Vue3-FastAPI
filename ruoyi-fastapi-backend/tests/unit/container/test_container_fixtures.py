from __future__ import annotations


def test_app_container_fixture_supports_override(app_container) -> None:
    marker = object()
    app_container.override('project_service', lambda _session: marker)

    resolved = app_container.resolve_service('project_service', session=object())  # type: ignore[arg-type]
    assert resolved is marker


def test_app_container_in_server_fixture_mounts_container(app_container_in_server) -> None:
    from server import app

    assert getattr(app.state, 'container', None) is app_container_in_server
