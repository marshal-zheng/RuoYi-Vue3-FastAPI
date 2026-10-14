"""Collection response declarations must describe the real response factory wire format."""

import json

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from pydantic import TypeAdapter, ValidationError

from module_admin.controller.device_category_controller import device_category_router
from modules.system.api.cache_controller import cache_router
from modules.system.api.dept_controller import deptController
from modules.system.api.dict_controller import dictController
from modules.system.api.menu_controller import menuController
from utils.response_util import ResponseUtil


@pytest.mark.parametrize(
    ('router', 'path', 'row'),
    [
        (menuController, '/system/menu/list', {'menuId': 1, 'menuName': 'Menu'}),
        (deptController, '/system/dept/list', {'deptId': 2, 'deptName': 'Dept'}),
        (deptController, '/system/dept/list/exclude/{dept_id}', {'deptId': 2, 'deptName': 'Dept'}),
        (dictController, '/system/dict/type/optionselect', {'dictId': 3, 'dictType': 'status'}),
        (device_category_router, '/device/category/options', {'deviceCategoryId': 8, 'name': 'Network'}),
        (cache_router, '/monitor/cache/getNames', {'cacheName': 'user', 'remark': 'User cache'}),
        (cache_router, '/monitor/cache/getKeys/{cache_name}', 'user:7'),
    ],
)
def test_collection_schema_validates_factory_payload_and_rejects_bare_arrays(router, path, row):
    app = FastAPI()
    app.include_router(router)
    route = next(route for route in app.routes if isinstance(route, APIRoute) and route.path == path)
    payload = json.loads(ResponseUtil.ok_resource([row]).body)

    adapter = TypeAdapter(route.response_model)
    validated = adapter.validate_python(payload)
    item = validated.model_dump(by_alias=True)['items'][0]
    if isinstance(row, dict):
        assert item.items() >= row.items()
    else:
        assert item == row
    with pytest.raises(ValidationError):
        adapter.validate_python([row])
    with pytest.raises(ValidationError):
        adapter.validate_python({})

    schema = app.openapi()
    response_schema = schema['paths'][path]['get']['responses']['200']['content']['application/json']['schema']
    collection = schema['components']['schemas'][response_schema['$ref'].rsplit('/', 1)[1]]
    assert collection['type'] == 'object'
    assert 'items' in collection['required']
    item_schema = collection['properties']['items']['items']
    if isinstance(row, dict):
        assert '$ref' in item_schema
    else:
        assert item_schema['type'] == 'string'
