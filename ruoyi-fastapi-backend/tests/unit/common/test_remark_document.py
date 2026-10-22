"""The shared vectors are independent of the runtime validator."""

import json
from pathlib import Path

import pytest

from common import remark_document_v1
from module_admin.entity.vo.remark_vo import RemarkDocument

ROOT = Path(__file__).resolve().parents[4] / 'shared/remarks/remark-a-v1'


@pytest.mark.parametrize(
    'vector', json.loads((ROOT / 'manifest.json').read_text())['vectors'], ids=lambda vector: vector['file']
)
def test_shared_vectors(vector):
    c = remark_document_v1
    value = json.loads((ROOT / vector['file']).read_text())
    if vector['file'].startswith('invalid/'):
        with pytest.raises(ValueError):
            c.validate_remark(value)
    elif vector['file'].startswith('plaintext/'):
        result = c.plain_to_remark(value['text'], identity_key=value['identityKey'])
        assert result == value['expected']
        assert c.remark_literal_text(result) == value['literal']
        assert c.plain_to_remark(value['text'], identity_key=value['identityKey']) == result
    else:
        result = c.validate_remark(value)
        assert result == vector.get('normalized', value)
        assert c.remark_literal_text(result) == vector['literal']
        assert c.remark_display_text(result) == vector['display']


def test_character_and_raw_depth_budget_before_recursion():
    c = remark_document_v1
    assert c.remark_literal_text(c.plain_to_remark('😀' * 5000, identity_key='x')) == '😀' * 5000
    with pytest.raises(ValueError, match='characters'):
        c.plain_to_remark('😀' * 5001, identity_key='x')
    value = {}
    for _ in range(100):
        value = {'nested': value}
    with pytest.raises(ValueError, match='container-depth'):
        c.validate_remark(value)
    with pytest.raises(ValueError, match='unicode'):
        c.plain_to_remark('\ud800', identity_key='x')


def test_vo_serialization_preserves_null_attributes_and_omission():
    c = remark_document_v1
    raw = c.plain_to_remark('x', identity_key='x')
    model = RemarkDocument.model_validate(raw)
    assert c.remark_to_storage(model) == raw
    assert model.model_dump()['body']['content']['content'][0]['attrs']['textAlign'] is None
