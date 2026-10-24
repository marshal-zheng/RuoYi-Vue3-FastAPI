"""User controller contract tests for the repository-based architecture."""

from modules.system.api.user_controller import userController


def _route_map(router):
    return {
        (route.path, tuple(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"})))
        for route in router.routes
    }


def test_user_router_registers_core_crud_endpoints():
    routes = _route_map(userController)
    assert ("/system/user/list", ("GET",)) in routes
    assert ("/system/user", ("POST",)) in routes
    assert ("/system/user", ("PUT",)) in routes
    assert ("/system/user/{user_ids}", ("DELETE",)) in routes


def test_user_router_registers_profile_and_status_endpoints():
    routes = _route_map(userController)
    assert ("/system/user/profile", ("GET",)) in routes
    assert ("/system/user/changeStatus", ("PUT",)) in routes
    assert ("/system/user/resetPwd", ("PUT",)) in routes
