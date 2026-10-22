"""Database failure paths and database audits exclude remark body values."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from common.remark_document_v1 import plain_to_remark
from module_admin.entity.do.role_do import RoleDO
from tests.integration.test_remark_log_privacy import SENTINEL, database_failure
from utils import audit_logger
from utils.log_safety import log_safe_exception, redact_document_data, safe_exception_summary
from utils.log_util import logger
from utils.transaction_manager import TransactionManager


@pytest.mark.parametrize('mode', ['new', 'nested', 'joined'])
async def test_transaction_failure_logs_do_not_serialize_document_parameters(test_engine, mode):
    messages = []
    sink = logger.add(lambda message: messages.append(str(message)), serialize=True, diagnose=True, backtrace=True)
    try:
        async with AsyncSession(test_engine) as session:
            if mode != 'new':
                await session.begin()
            with pytest.raises(type(database_failure())):
                async with TransactionManager(session).transaction(savepoint=mode == 'nested'):
                    raise database_failure()
        assert SENTINEL not in '\n'.join(messages)
        assert 'StatementError' in '\n'.join(messages)
    finally:
        logger.remove(sink)


def test_database_audit_does_not_store_authoritative_document_body():
    row = RoleDO(
        role_id=77, role_name='Private', role_key='private', remark=plain_to_remark(SENTINEL, identity_key='r')
    )
    value = audit_logger._serialize_instance(row)
    assert value['role_name'] == 'Private'
    assert SENTINEL not in json.dumps(value)


@pytest.mark.parametrize('shape', ['envelope', 'body', 'tree', 'json-string'])
def test_arbitrary_generated_document_fields_and_derived_text_are_redacted(shape):
    document = plain_to_remark(SENTINEL, identity_key='generated:1:review_notes')
    values = {
        'envelope': document,
        'body': document['body'],
        'tree': document['body']['content'],
        'json-string': json.dumps(document),
    }
    original = {'recordId': 7, 'reviewNotes': values[shape], 'reviewNotesText': SENTINEL, 'password': 'private'}
    result = redact_document_data(original, mask_fields={'password'})
    assert result['recordId'] == 7
    assert SENTINEL not in json.dumps(result)
    assert 'private' not in json.dumps(result)
    assert original['reviewNotesText'] == SENTINEL


def test_database_exception_groups_use_the_same_safe_integer_diagnostics():
    error = ExceptionGroup('requests failed', [database_failure()])
    summary = safe_exception_summary(error)
    assert summary == 'StatementError (db_code=1213)'
    assert SENTINEL not in summary


def test_non_database_exceptions_keep_the_existing_diagnostic_trace():
    messages = []
    sink = logger.add(lambda message: messages.append(str(message)), serialize=True, diagnose=True, backtrace=True)

    def fail(_document):
        raise RuntimeError('ordinary diagnostic')

    doc = plain_to_remark(SENTINEL, identity_key='trace:1')
    try:
        try:
            fail(doc)
        except RuntimeError as error:
            log_safe_exception(logger, 'ordinary failure', error)
        text = '\n'.join(messages)
        assert 'ordinary diagnostic' in text
        assert 'RuntimeError' in text
        assert 'test_non_database_exceptions_keep_the_existing_diagnostic_trace' in text
        assert SENTINEL not in text
    finally:
        logger.remove(sink)
