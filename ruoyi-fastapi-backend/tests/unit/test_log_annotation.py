from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType
from module_admin.annotation import log_annotation


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('content_type', 'expected'),
    [
        ('application/x-www-form-urlencoded', 'userId: 7\nroleIds: 2'),
        ('application/json', '{"userId": "7", "roleIds": "2"}'),
    ],
)
async def test_query_only_writes_keep_existing_operation_log_parameters(monkeypatch, content_type, expected):
    service = SimpleNamespace(add_operation_log_services=AsyncMock())
    user = SimpleNamespace(user=SimpleNamespace(user_name='operator', dept=None))
    monkeypatch.setattr(log_annotation, '_is_test_env', lambda: False)
    monkeypatch.setattr(log_annotation, '_resolve_request_service', lambda *_args: service)
    monkeypatch.setattr(log_annotation.LoginService, 'get_current_user', AsyncMock(return_value=user))
    monkeypatch.setattr(log_annotation.AppConfig, 'app_ip_location_query', False)

    @log_annotation.Log(title='参数兼容', business_type=BusinessType.GRANT)
    async def endpoint(request: Request, query_db: AsyncSession):
        return log_annotation.ResponseUtil.no_content()

    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    request = Request(
        {
            'type': 'http',
            'method': 'PUT',
            'path': '/sample',
            'query_string': b'userId=7&roleIds=2',
            'headers': [
                (b'content-type', content_type.encode()),
                (b'user-agent', b'test'),
                (b'x-forwarded-for', b'127.0.0.1'),
            ],
        },
        receive,
    )

    response = await endpoint(request, AsyncMock(spec=AsyncSession))

    assert response.status_code == 204
    service.add_operation_log_services.assert_awaited_once()
    assert service.add_operation_log_services.await_args.args[0].oper_param == expected
