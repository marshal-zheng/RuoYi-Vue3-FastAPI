"""Config controller contract tests for the repository-based architecture."""

from modules.system.api.config_controller import configController


def _route_map(router):
    return {
        (route.path, tuple(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"})))
        for route in router.routes
    }


def test_config_router_registers_core_crud_endpoints():
    routes = _route_map(configController)
    assert ("/system/config/list", ("GET",)) in routes
    assert ("/system/config", ("POST",)) in routes
    assert ("/system/config", ("PUT",)) in routes
    assert ("/system/config/{config_ids}", ("DELETE",)) in routes


def test_config_router_registers_read_helpers():
    routes = _route_map(configController)
    assert ("/system/config/{config_id}", ("GET",)) in routes
    assert ("/system/config/configKey/{config_key}", ("GET",)) in routes
    assert ("/system/config/export", ("POST",)) in routes
