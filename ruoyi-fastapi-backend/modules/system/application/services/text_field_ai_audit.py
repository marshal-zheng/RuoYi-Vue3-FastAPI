# ruff: noqa: PLC0415 -- Audit persistence is loaded only at finalization.
"""Allowlist-only generation audit, finalized by the outer ASGI boundary exactly once per attempt."""

import json
from datetime import datetime


async def write_ai_audit(record: dict):
    # Lazy imports: application startup and unavailable status never open an audit DB session.
    from config.get_db import get_session_factory
    from module_admin.entity.vo.log_vo import OperLogModel
    from modules.system.application.services.log_service import OperationLogService
    from modules.system.infrastructure.log_repository import OperLogRepository

    async with get_session_factory()() as session:
        service = OperationLogService(OperLogRepository(session), session)
        await service.add_operation_log_services(
            OperLogModel(
                title='文本字段 AI',
                business_type=0,
                method='text_field_ai.generate',
                request_method='POST',
                operator_type=1,
                oper_name=str(record['userId']),
                oper_url='/system/ai/text-field/generate',
                oper_param=json.dumps(record, ensure_ascii=False, separators=(',', ':')),
                status=0 if record['outcome'] == 'completed' else 1,
                oper_time=datetime.now(),
                cost_time=record['latencyMs'],
            )
        )
