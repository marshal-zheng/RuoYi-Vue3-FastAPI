"""Role controller contract tests for the repository-based architecture."""

from modules.system.api.role_controller import roleController


def _route_map(router):
    return {
        (route.path, tuple(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"})))
        for route in router.routes
    }


def test_role_router_registers_core_crud_endpoints():
    routes = _route_map(roleController)
    assert ("/system/role/list", ("GET",)) in routes
    assert ("/system/role", ("POST",)) in routes
    assert ("/system/role", ("PUT",)) in routes
    assert ("/system/role/{role_ids}", ("DELETE",)) in routes


def test_role_router_registers_permission_endpoints():
    routes = _route_map(roleController)
    assert ("/system/role/changeStatus", ("PUT",)) in routes
    assert ("/system/role/dataScope", ("PUT",)) in routes
    assert ("/system/role/deptTree/{role_id}", ("GET",)) in routes
