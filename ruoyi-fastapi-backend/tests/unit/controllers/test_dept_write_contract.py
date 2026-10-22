"""Department HTTP writes use the actual registered request models."""

import pytest
from pydantic import ValidationError

from modules.system.api.dept_controller import deptController


def body_model(method):
    return next(r.body_field.type_ for r in deptController.routes if r.path == '/system/dept' and method in r.methods)


def payload(method):
    return {'parentId': 0, 'deptName': '部门', 'orderNum': 0, **({'deptId': 42} if method == 'PUT' else {})}


@pytest.mark.parametrize('method', ['POST', 'PUT'])
@pytest.mark.parametrize(
    'field,value',
    [
        ('delFlag', '2'),
        ('ancestors', '0,999'),
        ('createBy', 'forged'),
        ('createTime', '2020-01-01T00:00:00'),
        ('updateBy', 'forged'),
        ('updateTime', '2020-01-01T00:00:00'),
        ('admin', True),
    ],
)
def test_rejects_server_owned_and_unknown_fields(method, field, value):
    with pytest.raises(ValidationError):
        body_model(method)(**payload(method), **{field: value})


@pytest.mark.parametrize('value', ['missing', None, 0, -1])
def test_update_requires_positive_identity(value):
    data = payload('PUT')
    if value == 'missing':
        data.pop('deptId')
    else:
        data['deptId'] = value
    with pytest.raises(ValidationError):
        body_model('PUT')(**data)


def test_create_rejects_client_identity():
    with pytest.raises(ValidationError):
        body_model('POST')(**payload('POST'), deptId=42)


@pytest.mark.parametrize('field', ['parentId', 'deptName', 'orderNum'])
def test_create_requires_business_fields(field):
    data = payload('POST')
    data.pop(field)
    with pytest.raises(ValidationError):
        body_model('POST')(**data)


@pytest.mark.parametrize('method', ['POST', 'PUT'])
@pytest.mark.parametrize(
    'field,value',
    [('parentId', None), ('parentId', -1), ('deptName', None), ('deptName', ' '), ('orderNum', None), ('status', None)],
)
def test_rejects_invalid_structural_fields(method, field, value):
    with pytest.raises(ValidationError):
        body_model(method)(**{**payload(method), field: value})


def test_partial_update_preserves_omission_and_allows_clearing_contacts():
    model = body_model('PUT')(deptId=42, phone=None, email='', leader=None)
    assert model.model_dump(exclude_unset=True) == {'dept_id': 42, 'phone': None, 'email': '', 'leader': None}


@pytest.mark.parametrize('method', ['POST', 'PUT'])
def test_root_and_zero_order_are_valid(method):
    model = body_model(method)(**payload(method))
    assert model.parent_id == model.order_num == 0
