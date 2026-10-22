"""Valid remarks must not escape through SQL failure logs or operation audits."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import StatementError

from common.remark_document_v1 import plain_to_remark
from exceptions.handle import handle_exception
from module_admin.annotation import log_annotation
from module_admin.entity.do.log_do import OperLogDO
from module_admin.entity.vo.post_vo import PostModel
from modules.system.infrastructure.log_repository import OperLogRepository
from modules.system.infrastructure.post_repository import PostRepository
from server import app
from utils.log_util import logger

SENTINEL = 'SENSITIVE_REMARK_SENTINEL_9df23c'


def document():
    return plain_to_remark(SENTINEL, identity_key='sys_post:77:remark')


def database_failure():
    return StatementError(
        'write failed',
        'INSERT INTO sys_post (remark) VALUES (:remark)',
        {'remark': document()},
        Exception(1213, f'driver message {SENTINEL}'),
    )


@pytest.fixture
def privacy_logs():
    messages = []
    sink = logger.add(lambda message: messages.append(str(message)), serialize=True, diagnose=True, backtrace=True)
    try:
        yield messages
    finally:
        logger.remove(sink)


@pytest.fixture
def real_operation_audit(monkeypatch):
    monkeypatch.setattr(log_annotation, '_is_test_env', lambda: False)
    monkeypatch.setattr(log_annotation.AppConfig, 'app_ip_location_query', False)
    actor = SimpleNamespace(user=SimpleNamespace(user_name='admin', dept=None))
    monkeypatch.setattr(log_annotation.LoginService, 'get_current_user', AsyncMock(return_value=actor))
    original_add = OperLogRepository.add

    async def insert_with_sqlite_identity(self, value):
        # SQLite does not generate BigInteger identities. Preserve the real
        # repository/session and give only this test audit an explicit identity.
        value.oper_id = 9001
        return await original_add(self, value)

    monkeypatch.setattr(OperLogRepository, 'add', insert_with_sqlite_identity)


async def test_legal_document_sql_failure_logs_and_persisted_failure_audit_are_private(
    remark_http, real_operation_audit, monkeypatch, privacy_logs
):
    async def fail_add(_self, _value):
        raise database_failure()

    monkeypatch.setattr(PostRepository, 'add', fail_add)
    response = await remark_http.post(
        '/system/post', json={'postName': 'Private', 'postCode': 'private', 'postSort': 1, 'remark': document()}
    )
    assert response.status_code == 500, response.text
    async with app.state.container._session_factory() as session:
        audit = (await session.scalars(select(OperLogDO))).one()
        assert audit.status == 1
        assert audit.oper_name == 'admin'
        assert json.loads(audit.oper_param)['postCode'] == 'private'
        assert SENTINEL not in audit.oper_param
        assert SENTINEL not in audit.json_result
        assert SENTINEL not in audit.error_msg
    text = '\n'.join(privacy_logs)
    assert SENTINEL not in response.text
    assert SENTINEL not in text
    assert 'StatementError' in text
    assert '1213' in text


async def test_successful_operation_request_and_response_audits_do_not_store_document_body(
    remark_http, real_operation_audit, privacy_logs
):
    response = await remark_http.post(
        '/system/post', json={'postName': 'Private', 'postCode': 'private', 'postSort': 1, 'remark': document()}
    )
    assert response.status_code == 201, response.text
    assert response.json()['remark'] == document()
    async with app.state.container._session_factory() as session:
        audit = (await session.scalars(select(OperLogDO))).one()
        assert audit.status == 0
        assert json.loads(audit.oper_param)['postCode'] == 'private'
        assert json.loads(audit.json_result)['postCode'] == 'private'
        assert SENTINEL not in audit.oper_param
        assert SENTINEL not in audit.json_result
    assert SENTINEL not in '\n'.join(privacy_logs)


async def test_generic_http_handler_never_logs_sqlalchemy_parameters(privacy_logs):
    sample = FastAPI()
    handle_exception(sample)

    @sample.post('/database-failure')
    async def endpoint(value: PostModel):
        assert value.remark is not None
        raise database_failure()

    async with AsyncClient(
        transport=ASGITransport(app=sample, raise_app_exceptions=False), base_url='http://test'
    ) as client:
        response = await client.post('/database-failure', json={'remark': document()})
    assert response.status_code == 500, response.text
    text = '\n'.join(privacy_logs)
    assert SENTINEL not in response.text
    assert SENTINEL not in text
    assert 'StatementError' in text
    assert '1213' in text


async def test_query_pipeline_sql_failure_keeps_correlation_without_document_parameters(
    remark_http, monkeypatch, privacy_logs
):
    async def fail_query(_self, **_filters):
        raise database_failure()

    monkeypatch.setattr(PostRepository, 'paginate_with_filters', fail_query)
    response = await remark_http.get('/system/post/list')
    assert response.status_code == 500, response.text
    text = '\n'.join(privacy_logs)
    assert SENTINEL not in response.text
    assert SENTINEL not in text
    assert 'cqrs_query_failed' in text
    assert 'StatementError' in text
    assert '1213' in text
