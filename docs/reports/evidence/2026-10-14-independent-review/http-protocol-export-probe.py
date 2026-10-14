import asyncio
import inspect
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
sys.path.insert(0, os.getcwd())
import httpx
from fastapi import FastAPI
from fastapi.routing import APIRoute
from module_admin.controller.protocol_controller import export_protocol_config
from module_admin.service.protocol_service import ProtocolService

async def main():
    app = FastAPI()
    app.post('/system/protocol/export')(inspect.unwrap(export_protocol_config))
    service = AsyncMock(spec=ProtocolService)
    service.export_protocol_config_services.return_value = {'protocol_name':'Test','content':b'PK\x03\x04valid-test'}
    route = next(r for r in app.routes if isinstance(r,APIRoute))
    for dependency in route.dependant.dependencies:
        app.dependency_overrides[dependency.call] = lambda: service
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        wrong = await client.post('/system/protocol/export',json={'protocolId':7})
        fixed = await client.post('/system/protocol/export',data={'protocolId':'7'})
    result = {
        'jsonBody':{'status':wrong.status_code,'body':wrong.json()},
        'formBody':{'status':fixed.status_code,'contentType':fixed.headers.get('content-type'),'bodyHex':fixed.content.hex()},
        'serviceCalls':[[list(args),kwargs] for args,kwargs in service.export_protocol_config_services.await_args_list],
        'normalDbWrites':0,
        'note':'Fresh FastAPI ASGI app uses the real undecorated business endpoint signature/body parsing/response and a service double; removed operation log only.'
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))
    Path('/tmp/independent-protocol-export-probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    assert wrong.status_code==422 and fixed.status_code==200
    assert fixed.content==b'PK\x03\x04valid-test'
    service.export_protocol_config_services.assert_awaited_once_with(7)

asyncio.run(main())
