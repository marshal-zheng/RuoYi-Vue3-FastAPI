"""Remark validation keeps typed error causes and prevents partial HTTP updates."""

import json
from pathlib import Path

import pytest

from common.remark_document_v1 import plain_to_remark

ROOT = Path(__file__).resolve().parents[3] / 'shared/remarks/remark-a-v1'


@pytest.mark.parametrize(
    ('filename', 'code', 'field'),
    [
        ('version', 'remark_version', 'remark'),
        ('missing-attribute', 'remark_structure', 'remark.body.content.content.0'),
        ('link-0', 'remark_link', 'remark.body.content.content.0.content.0.marks.0.attrs.href'),
        ('characters-5001', 'remark_budget', 'remark'),
    ],
)
async def test_typed_remark_http_errors_have_paths_and_cannot_partially_update(remark_http, filename, code, field):
    document = plain_to_remark('authoritative', identity_key='sys_post:77:remark')
    created = await remark_http.post(
        '/system/post',
        json={'postName': 'Original', 'postCode': 'error_test', 'postSort': 1, 'remark': document},
    )
    assert created.status_code == 201, created.text
    post_id = created.json()['postId']
    invalid = json.loads((ROOT / f'invalid/{filename}.json').read_text())
    response = await remark_http.put(
        '/system/post',
        json={
            'postId': post_id,
            'postName': 'MUST_NOT_BE_SAVED',
            'postCode': 'error_test',
            'postSort': 1,
            'remark': invalid,
        },
    )
    assert response.status_code == 422, response.text
    problem = response.json()
    assert problem['errors'][0]['code'] == code
    assert problem['errors'][0]['field'] == field
    assert 'MUST_NOT_BE_SAVED' not in response.text
    assert '😀' not in response.text
    loaded = await remark_http.get(f'/system/post/{post_id}')
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()['postName'] == 'Original'
    assert loaded.json()['remark'] == document


@pytest.mark.parametrize('name', ['remarkText', 'remark_text'])
async def test_guarded_readonly_remark_input_is_field_located(remark_http, name):
    response = await remark_http.post(
        '/system/post', json={'postName': 'Readonly', 'postCode': 'readonly', 'postSort': 1, name: 'forged'}
    )
    assert response.status_code == 422, response.text
    error = response.json()['errors'][0]
    assert error['field'] == 'remarkText'
    assert error['code'] == 'remark_readonly'
    assert 'forged' not in response.text
