"""Retained grammar-default and preview regressions from the replaced protocol implementation."""

import json

import pytest

from common.remark_document_v1 import remark_literal_text, validate_remark
from modules.system.application.services.ai_providers.base import AIError
from modules.system.application.services.text_field_ai_document import normalize_output, preview_text
from tests.unit.services.test_text_field_ai import text_root


def test_normalization_admits_named_color_bold_link_and_preserves_text():
    marks = [
        {'type': 'textStyle', 'attrs': {'color': 'red'}},
        {'type': 'bold'},
        {'type': 'link', 'attrs': {'href': 'https://example.com/docs'}},
    ]
    result = normalize_output(json.dumps(text_root(marks=marks)))
    assert validate_remark(result) == result
    assert remark_literal_text(result) == '负责设备维护'
    node = result['body']['content']['content'][0]
    assert node['attrs']['blockId'].startswith('blk_')
    assert [mark['type'] for mark in node['content'][0]['marks']] == ['link', 'textStyle', 'bold']
    assert normalize_output(json.dumps(text_root(marks=marks))) != result  # A new candidate owns new block ids.


@pytest.mark.parametrize(
    'root',
    [
        {'type': 'doc', 'content': [{'type': 'image', 'attrs': {'src': 'https://example.com/a.png'}}]},
        text_root(marks=[{'type': 'underline'}]),
        text_root(marks=[{'type': 'link', 'attrs': {'href': 'javascript:alert(1)'}}]),
        text_root(marks=[{'type': 'textStyle', 'attrs': {'color': '#ff0000'}}]),
        text_root(marks=[{'type': 'textStyle', 'attrs': {'color': 'red', 'fontSize': '40px'}}]),
        {'type': 'doc', 'content': [{'type': 'paragraph'}]},
        {'type': 'doc', 'content': [{'type': 'paragraph', 'attrs': {'textAlign': 'center'}}]},
        {'type': 'doc', 'content': [{'type': 'orderedList', 'attrs': {'start': 0}, 'content': []}]},
    ],
)
def test_normalization_rejects_unsupported_and_empty_documents(root):
    with pytest.raises(AIError):
        normalize_output(json.dumps(root))


def test_normalization_rejects_character_limit_without_truncation():
    with pytest.raises(AIError, match='output-limit'):
        normalize_output(json.dumps(text_root('中' * 5001)))


def test_partial_json_preview_handles_unicode_escapes_and_only_reads_content():
    content = json.dumps({'document': text_root('中文😀"引号"\\'), 'notices': []}, ensure_ascii=True)
    prior = ''
    for size in range(1, len(content) + 1):
        current = preview_text(content[:size])
        if current.startswith(prior):
            prior = current
    assert prior == '中文😀"引号"\\'
    assert preview_text('{"type":"doc","reasoning_content":"private","content":[') == ''
