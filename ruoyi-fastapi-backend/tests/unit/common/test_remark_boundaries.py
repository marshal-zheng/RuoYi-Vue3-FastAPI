"""Independent resource-counting and API projection boundary probes."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from common import remark_document_v1 as codec
from module_admin.entity.vo.remark_vo import RemarkValue
from modules.system.application.read_models.post_read_models import PostDetailReadModel

ROOT = Path(__file__).resolve().parents[4] / 'shared/remarks/remark-a-v1'


def fixture(name):
    return json.loads((ROOT / name).read_text())


def compact_bytes(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())


def test_fixture_resource_boundaries_are_the_declared_sizes():
    assert compact_bytes(fixture('valid/bytes-262144.json')) == codec.LIMITS['bytes']
    assert compact_bytes(fixture('invalid/bytes-262145.json')) == codec.LIMITS['bytes'] + 1
    nodes = fixture('valid/nodes-2000.json')['body']['content']['content'][0]['content']
    assert len(nodes) + 2 == codec.LIMITS['nodes']
    href = fixture('valid/href-2048.json')['body']['content']['content'][0]['content'][0]['marks'][0]['attrs']['href']
    assert len(href) == codec.LIMITS['href']


def test_character_budget_counts_structural_lf_and_astral_code_points():
    value = codec.plain_to_remark('😀' * 4999, identity_key='boundary')
    content = value['body']['content']['content'][0]['content']
    content.append({'type': 'hardBreak'})
    assert len(codec.remark_literal_text(codec.validate_remark(value))) == 5000
    content.append({'type': 'hardBreak'})
    with pytest.raises(codec.RemarkError, match='characters'):
        codec.validate_remark(value)


def test_href_budget_counts_code_points_instead_of_utf8_bytes():
    prefix = 'https://example.com/'
    href = prefix + '😀' * (2048 - len(prefix))
    assert len(href.encode()) > 2048
    assert codec.validate_href(href) == href
    with pytest.raises(codec.RemarkError, match='link-length'):
        codec.validate_href(href + '😀')


def test_node_budget_applies_before_adjacent_text_canonicalization():
    value = codec.plain_to_remark('x', identity_key='boundary')
    value['body']['content']['content'][0]['content'] = [{'type': 'text', 'text': 'x'} for _ in range(1999)]
    with pytest.raises(codec.RemarkError, match='nodes'):
        codec.validate_remark(value)
    value['body']['content']['content'][0]['content'].pop()
    canonical = codec.validate_remark(value)
    assert canonical['body']['content']['content'][0]['content'] == [{'type': 'text', 'text': 'x' * 1998}]


def test_byte_budget_applies_before_canonicalization():
    value = fixture('valid/href-2048.json')
    text = value['body']['content']['content'][0]['content'][0]
    value['body']['content']['content'][0]['content'] = [deepcopy(text) for _ in range(140)]
    assert compact_bytes(value) > 262144
    with pytest.raises(codec.RemarkError, match='bytes'):
        codec.validate_remark(value)
    value['body']['content']['content'][0]['content'] = [deepcopy(text)]
    value['body']['content']['content'][0]['content'][0]['text'] *= 140
    assert codec.validate_remark(value) == value


def test_container_depth_guard_precedes_grammar_and_pydantic_recursion():
    value = 0
    for _ in range(32):
        value = {'nested': value}
    with pytest.raises(codec.RemarkError, match='structure'):
        codec.validate_remark(value)
    value = {'nested': value}
    with pytest.raises(codec.RemarkError, match='container-depth'):
        codec.validate_remark(value)
    for _ in range(1000):
        value = {'nested': value}

    class Request(BaseModel):
        remark: RemarkValue

    with pytest.raises(ValidationError) as failure:
        Request(remark=value)
    assert failure.value.errors(include_input=False)[0]['loc'] == ('remark',)
    assert 'container-depth' in failure.value.errors(include_input=False)[0]['msg']


def test_resource_iteration_guard_has_an_explicit_boundary():
    with pytest.raises(codec.RemarkError, match='structure'):
        codec.validate_remark({'unused': [None] * 49998})
    with pytest.raises(codec.RemarkError, match='resource-limit'):
        codec.validate_remark({'unused': [None] * 49999})


def test_legal_grammar_depth_counting_and_preventive_limits(monkeypatch):
    value = fixture('valid/list-depth-3.json')
    node = value['body']['content']
    while node['type'] != 'text':
        node = node['content'][-1]
    node['marks'] = fixture('valid/href-2048.json')['body']['content']['content'][0]['content'][0]['marks']
    # A's 3-list grammar reaches 9 node levels and 22 object/array levels.
    monkeypatch.setitem(codec.LIMITS, 'tree_depth', 9)
    monkeypatch.setitem(codec.LIMITS, 'container_depth', 22)
    assert codec.validate_remark(value) == value
    monkeypatch.setitem(codec.LIMITS, 'tree_depth', 8)
    with pytest.raises(codec.RemarkError, match='tree-depth'):
        codec.validate_remark(value)
    monkeypatch.setitem(codec.LIMITS, 'tree_depth', 12)
    monkeypatch.setitem(codec.LIMITS, 'container_depth', 21)
    with pytest.raises(codec.RemarkError, match='container-depth'):
        codec.validate_remark(value)


@pytest.mark.parametrize('name', ['valid/empty.json', 'valid/optional-array-canonical.json', 'valid/marks-break.json'])
def test_recursive_models_keep_the_codec_canonical_serialization(name):
    value = fixture(name)
    canonical = codec.validate_remark(value)
    parsed = TypeAdapter(RemarkValue).validate_python(value)
    assert codec.remark_to_storage(parsed) == canonical


def test_read_projection_ignores_forged_derived_input_and_recomputes_from_document():
    value = codec.plain_to_remark('authoritative', identity_key='post:1:remark')
    read = PostDetailReadModel(postId=1, remark=value, remarkText='forged')
    assert read.model_dump(by_alias=True)['remarkText'] == 'authoritative'
    assert PostDetailReadModel.model_validate(read.model_dump(by_alias=True)).remark_text == 'authoritative'


def test_invalid_link_error_does_not_include_the_submitted_body():
    value = fixture('invalid/link-invalid-utf8.json')
    value['body']['content']['content'][0]['content'][0]['text'] = 'PRIVATE_BODY_SENTINEL'
    with pytest.raises(codec.RemarkError) as failure:
        codec.validate_remark(value)
    assert 'PRIVATE_BODY_SENTINEL' not in str(failure.value)
    assert '%FF' not in str(failure.value)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf'), object()])
def test_non_json_values_do_not_escape_as_unhandled_encoding_errors(value):
    with pytest.raises(codec.RemarkError):
        codec.validate_remark({'unused': value})


def test_python_strict_integer_rejects_an_explicit_float_without_coercion():
    # JSON.parse maps both 1 and 1.0 to JavaScript Number(1). The shared JSON
    # vector uses 1.5; this Python-only probe retains the design's StrictInt rule.
    value = fixture('valid/nested-list.json')
    value['body']['content']['content'][0]['attrs']['start'] = 1.0
    with pytest.raises(codec.RemarkError, match='list-start'):
        codec.validate_remark(value)
