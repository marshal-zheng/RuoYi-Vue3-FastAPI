"""The published schema distinguishes document writes and computed read text."""

import pytest

from scripts.export_openapi import build_openapi_schema


@pytest.fixture(scope='module')
def schema():
    return build_openapi_schema()


@pytest.mark.parametrize(
    'name',
    [
        'UserCreateModel',
        'UserUpdateModel',
        'RoleCreateModel',
        'RoleUpdateModel',
        'PostModel',
        'DictTypeModel',
        'DictDataModel',
        'ConfigModel',
        'EditGenTableModel',
    ],
)
def test_write_schema_is_an_explicit_optional_document_and_has_no_derived_authority(schema, name):
    model = schema['components']['schemas'][name]
    assert model['properties']['remark']['anyOf'] == [
        {'$ref': '#/components/schemas/RemarkDocument-Input'},
        {'type': 'null'},
    ]
    assert 'remark' not in model.get('required', [])
    assert 'remarkText' not in model['properties']


@pytest.mark.parametrize(
    'name',
    [
        'UserInfoModel',
        'UserInfoReadModel',
        'UserListItemReadModel',
        'RoleInfoModel',
        'SelectedRoleModel',
        'RoleItemReadModel',
        'RoleDetailReadModel',
        'PostItemReadModel',
        'PostDetailReadModel',
        'DictTypeDetailReadModel',
        'DictDataDetailReadModel',
        'ConfigDetailReadModel',
        'GenTableReadModel',
    ],
)
def test_all_public_read_projections_mark_server_text_readonly(schema, name):
    model = schema['components']['schemas'][name]
    assert model['properties']['remarkText']['readOnly'] is True
    assert model['properties']['remarkText']['type'] == 'string'
    assert 'remarkText' in model['required']
    assert model['properties']['remark']['anyOf'][0] == {'$ref': '#/components/schemas/RemarkDocument-Output'}


@pytest.mark.parametrize(
    'path',
    [
        '/system/user/list',
        '/system/role/list',
        '/system/post/list',
        '/system/dict/type/list',
        '/system/dict/data/list',
        '/system/config/list',
        '/tool/gen/list',
    ],
)
def test_get_query_contract_does_not_expand_the_recursive_document(schema, path):
    names = {parameter['name'] for parameter in schema['paths'][path]['get'].get('parameters', [])}
    assert 'remark' not in names
    assert 'remarkText' not in names


def test_document_schema_has_exact_outer_shape_and_empty_resources(schema):
    for name in ['RemarkDocument-Input', 'RemarkDocument-Output']:
        model = schema['components']['schemas'][name]
        assert model['additionalProperties'] is False
        assert set(model['properties']) == {'version', 'body', 'annotations', 'assets', 'meta'}
        assert set(model['required']) == set(model['properties'])
        assert model['properties']['version']['const'] == 2
        assert model['properties']['annotations']['maxItems'] == 0
        assert model['properties']['assets']['maxItems'] == 0


@pytest.mark.parametrize(
    'name', ['UserStatusUpdateModel', 'RoleStatusUpdateModel', 'RoleDataScopeUpdateModel', 'UserProfileUpdateModel']
)
def test_dedicated_writes_cannot_rewrite_remark(schema, name):
    model = schema['components']['schemas'][name]
    assert model['additionalProperties'] is False
    assert 'remark' not in model['properties']
    assert 'remarkText' not in model['properties']
