"""Authorization writes expose one fixed operation and JSON collection semantics."""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from pydantic import ValidationError

from modules.system.api.role_controller import roleController
from modules.system.api.user_controller import userController

CASES = [
    (userController, '/system/user/authRole', {'userId': 42, 'roleIds': [2, 3]}, 'roleIds', True),
    (roleController, '/system/role/authUser/selectAll', {'roleId': 2, 'userIds': [42, 43]}, 'userIds', False),
    (roleController, '/system/role/authUser/cancel', {'roleId': 2, 'userId': 42}, None, False),
    (roleController, '/system/role/authUser/cancelAll', {'roleId': 2, 'userIds': [42, 43]}, 'userIds', False),
]


def model_for(router, path):
    route = next(r for r in router.routes if r.path == path and 'PUT' in r.methods)
    assert route.body_field is not None, f'{path} must accept a typed JSON body'
    return route.body_field.type_


@pytest.mark.parametrize('router,path,valid,collection,allow_empty', CASES)
def test_operation_contract(router, path, valid, collection, allow_empty):
    model = model_for(router, path)
    assert model.model_validate(valid).model_dump(by_alias=True) == valid
    for key in {'userId', 'roleId', 'userIds', 'roleIds', 'admin', 'createBy'} - valid.keys():
        with pytest.raises(ValidationError):
            model.model_validate({**valid, key: None})
    for key in valid:
        for value in [None, 'missing']:
            payload = {**valid, key: value}
            if value == 'missing':
                payload.pop(key)
            with pytest.raises(ValidationError):
                model.model_validate(payload)
    for key in valid:
        for invalid in [0, -1, True, 1.5, '42', 2147483648]:
            value = [invalid] if key == collection else invalid
            with pytest.raises(ValidationError):
                model.model_validate({**valid, key: value})
    if collection:
        if allow_empty:
            assert model.model_validate({**valid, collection: []}).model_dump(by_alias=True)[collection] == []
        else:
            with pytest.raises(ValidationError):
                model.model_validate({**valid, collection: []})
        assert model.model_validate({**valid, collection: [42, 42, 43]}).model_dump(by_alias=True)[collection] == [
            42,
            43,
        ]
        with pytest.raises(ValidationError):
            model.model_validate({**valid, collection: '42,43'})


def test_each_operation_has_its_own_schema():
    assert len({model_for(router, path) for router, path, *_ in CASES}) == 4


def test_authorization_response_schemas_are_no_content():
    app = FastAPI()
    app.include_router(userController)
    app.include_router(roleController)
    schema = app.openapi()
    for _, path, *_ in CASES:
        response = schema['paths'][path]['put']['responses']
        assert '204' in response
        assert '200' not in response
        assert 'content' not in response['204']


@pytest.mark.parametrize('router,path,valid,collection,allow_empty', CASES)
def test_checked_in_openapi_matches_registered_authorization_contract(router, path, valid, collection, allow_empty):
    app = FastAPI()
    app.include_router(router)
    runtime = app.openapi()
    public = json.loads((Path(__file__).parents[4] / 'shared' / 'openapi.json').read_text())
    operation = runtime['paths'][path]['put']
    checked_in = public['paths'][path]['put']
    for section in ('requestBody', 'responses', 'parameters'):
        assert checked_in.get(section) == operation.get(section)
    model_name = model_for(router, path).__name__
    assert public['components']['schemas'][model_name] == runtime['components']['schemas'][model_name]
    assert 'CrudUserRoleModel' not in public['components']['schemas']
