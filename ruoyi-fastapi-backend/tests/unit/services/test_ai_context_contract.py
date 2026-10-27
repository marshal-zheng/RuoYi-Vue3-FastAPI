"""The same synthetic machine vectors as the TS consumer, admitted through actual Python public models."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from common.ai_context import PREFIXES, RESERVED, TOKEN
from config.error_codes import ErrorCode
from module_admin.entity.vo.text_field_ai_vo import TextFieldAIEvent, TextFieldAIRequest
from modules.system.api.text_field_ai_controller import HTTP_ERRORS
from modules.system.application.services.ai_context_manifest import Manifest

ROOT = Path(__file__).resolve().parents[4] / 'shared/ai-context'


def read(name):
    return json.loads((ROOT / name).read_text())


def vectors(folder):
    return [(path.name, json.loads(path.read_text())) for path in sorted((ROOT / 'vectors' / folder).glob('*.json'))]


@pytest.mark.parametrize('name,case', vectors('request'))
def test_shared_request_vectors_use_actual_vo(name, case):
    del name
    try:
        TextFieldAIRequest.model_validate(case['value'])
        valid = True
    except (ValidationError, ValueError):
        valid = False
    assert valid == case['valid']


@pytest.mark.parametrize('name,case', vectors('events'))
def test_shared_event_vectors_use_public_discriminated_union(name, case):
    del name
    try:
        TypeAdapter(TextFieldAIEvent).validate_python(case['value'])
        valid = True
    except (ValidationError, ValueError):
        valid = False
    assert valid == case['valid']


@pytest.mark.parametrize('name,case', vectors('manifest-cases'))
def test_shared_manifest_vectors_use_actual_loader_model(name, case):
    del name
    try:
        Manifest.model_validate(case['value'])
        valid = True
    except (ValidationError, ValueError):
        valid = False
    assert valid == case['valid']


def test_public_placeholder_grammar_matches_server_scanner():
    grammar = read('placeholder-grammar.json')
    assert grammar['prefixes'] == PREFIXES and grammar['reserved'] == list(RESERVED)
    for case in read('vectors/placeholders.json')['cases']:
        assert bool(TOKEN.fullmatch(case['value'])) == case['valid']


def test_http_vectors_match_actual_status_and_error_codes():
    for case in read('vectors/http/errors.json')['cases']:
        if case['expected'] == 'authentication':
            assert (case['status'], case['errorCode']) == (401, ErrorCode.UNAUTHORIZED)
        elif case['expected'] == 'quota-exceeded':
            assert (case['status'], case['errorCode']) == (429, 42901)
        else:
            assert HTTP_ERRORS[case['expected']] == (case['status'], case['errorCode'])


def test_shared_stream_frames_use_server_event_models():
    # Sequence/EOF rejection is exercised by the actual TS consumer, not a duplicate test-only FSM here.
    validator = TypeAdapter(TextFieldAIEvent)
    for case in read('vectors/streams/boundaries.json')['cases']:
        for event in case['events']:
            validator.validate_python(event)
