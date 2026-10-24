"""Record actual controller/factory response bytes without a database or any writes.

Run from ruoyi-fastapi-backend with its Python environment. Service dependencies
are read-only fixtures; controllers and ResponseUtil are the real backend code.
"""

import asyncio
import inspect
import json

from module_admin.controller import simulation_controller as controller
from utils.response_util import ResponseUtil
from starlette.requests import Request


class ReadOnlyService:
    async def start_session(self, session_id):
        return {'sessionId': session_id}

    async def stop_session(self, session_id):
        return {'sessionId': session_id}

    async def read_messages_with_fallback(self, *args):
        return [{'messageId': 'message-1', 'sendTimestamp': 1000, 'payloadHex': 'AA', 'fieldValues': {'sequence': 1}}]

    async def read_bandwidth_with_fallback(self, *args, **kwargs):
        return [{'timestamp': 1000, 'bandwidthMbps': 12, 'portId': 'port-1'}]

    async def read_alarms_with_fallback(self, *args):
        return [{
            'alarmId': 'alarm-1', 'timestamp': 1000, 'severity': 'warning', 'message': 'wire warning',
            'details': {'connections': [{'edgeId': 'edge-1'}]},
        }]

    def require_session_id(self, session_id):
        return session_id

    def list_faults(self, *args):
        return [{'faultId': 'fault-1', 'faultType': 'disconnect', 'targetId': 'edge-1', 'targetType': 'edge', 'status': 'active'}]

    def list_events(self, *args):
        return [{
            'eventId': 'event-1', 'name': 'Wire event', 'status': 'pending',
            'condition': {'type': 'time', 'value': {'time': 1}},
            'action': {'type': 'log', 'params': {'message': 'ready'}},
        }]


async def main():
    service = ReadOnlyService()
    replies = {}
    for name in ['get_simulation_messages', 'get_simulation_bandwidth', 'get_simulation_alarms', 'list_events', 'list_faults']:
        response = await getattr(controller, name)(request=None, session_id='session-1', simulation_service=service)
        replies[name] = json.loads(response.body)
    response = await controller.query_faults(session_id='session-1', simulation_service=service)
    replies['query_faults'] = json.loads(response.body)
    response = await controller.get_fill_strategies(request=None)
    replies['get_fill_strategies'] = json.loads(response.body)
    replies['embedded_resource'] = json.loads(ResponseUtil.ok_resource({'events': service.list_events()}).body)
    for action in ['start', 'stop']:
        # Skip audit logging decorators so no database-backed log records are written.
        endpoint = inspect.unwrap(getattr(controller, f'{action}_simulation_session'))
        request = Request({
            'type': 'http', 'scheme': 'http', 'method': 'POST',
            'server': ('127.0.0.1', 8088), 'headers': [],
            'path': f'/simulation/sessions/session-1/{action}', 'query_string': b'',
        })
        response = await endpoint(request=request, session_id='session-1', simulation_service=service)
        replies[f'{action}_accepted'] = {
            'body': json.loads(response.body),
            'status': response.status_code,
            'location': response.headers['location'],
        }
    print(json.dumps(replies, ensure_ascii=False, indent=2))


asyncio.run(main())
