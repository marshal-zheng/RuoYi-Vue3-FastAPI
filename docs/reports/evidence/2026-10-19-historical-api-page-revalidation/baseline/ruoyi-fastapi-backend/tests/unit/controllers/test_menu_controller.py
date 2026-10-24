"""Menu controller contract tests for the repository-based architecture."""

from modules.system.api.menu_controller import menuController


def _route_map(router):
    return {
        (route.path, tuple(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"})))
        for route in router.routes
    }


def test_menu_router_registers_core_crud_endpoints():
    routes = _route_map(menuController)
    assert ("/system/menu/list", ("GET",)) in routes
    assert ("/system/menu", ("POST",)) in routes
    assert ("/system/menu", ("PUT",)) in routes
    assert ("/system/menu/{menu_ids}", ("DELETE",)) in routes


def test_menu_router_registers_tree_endpoints():
    routes = _route_map(menuController)
    assert ("/system/menu/treeselect", ("GET",)) in routes
    assert ("/system/menu/roleMenuTreeselect/{role_id}", ("GET",)) in routes
    assert ("/system/menu/{menu_id}", ("GET",)) in routes
