"""Dept controller contract tests for the repository-based architecture."""

from modules.system.api.dept_controller import deptController


def _route_map(router):
    return {
        (route.path, tuple(sorted(m for m in route.methods if m not in {"HEAD", "OPTIONS"})))
        for route in router.routes
    }


def test_dept_router_registers_core_crud_endpoints():
    routes = _route_map(deptController)
    assert ("/system/dept/list", ("GET",)) in routes
    assert ("/system/dept", ("POST",)) in routes
    assert ("/system/dept", ("PUT",)) in routes
    assert ("/system/dept/{dept_ids}", ("DELETE",)) in routes


def test_dept_router_registers_tree_and_export_endpoints():
    routes = _route_map(deptController)
    assert ("/system/dept/treeselect", ("GET",)) in routes
    assert ("/system/dept/list/exclude/{dept_id}", ("GET",)) in routes
    assert ("/system/dept/export", ("POST",)) in routes
