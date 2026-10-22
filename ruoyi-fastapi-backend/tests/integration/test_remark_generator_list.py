"""Generator metadata lists validate native JSON before their JSONResponse boundary."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from module_generator.entity.do.gen_do import GenTableDO
from module_generator.entity.vo.gen_vo import GenTablePageQueryModel
from module_generator.repository.gen_repository import GenTableRepository
from module_generator.service.gen_service import GenTableService
from server import app

ROOT = Path(__file__).resolve().parents[3] / 'shared/remarks/remark-a-v1'


async def test_generator_http_list_projects_nested_document_and_authoritative_text(remark_http):
    document = json.loads((ROOT / 'valid/nested-list.json').read_text())
    async with app.state.container._session_factory() as session:
        session.add(GenTableDO(table_id=200, table_name='nested_note', table_comment='Nested', remark=document))
        await session.commit()
    response = await remark_http.get('/tool/gen/list')
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['total'] == 1
    assert payload['items'][0]['tableId'] == 200
    assert payload['items'][0]['remark'] == document
    assert payload['items'][0]['remarkText'] == '3. 第一\n  - 子项\n4. 第二'


@pytest.mark.parametrize(('remark', 'code'), [('legacy', 'remark_structure'), ({'bad': True}, 'remark_structure')])
async def test_generator_http_list_refuses_invalid_stored_documents(remark_http, remark, code):
    async with app.state.container._session_factory() as session:
        session.add(GenTableDO(table_id=201, table_name='bad_note', table_comment='Invalid', remark=remark))
        await session.commit()
    response = await remark_http.get('/tool/gen/list')
    assert response.status_code == 422, response.text
    assert response.json()['errors'][0]['code'] == code
    assert 'remark' in response.json()['errors'][0]['field']
    assert 'items' not in response.json()
    async with app.state.container._session_factory() as session:
        row = await session.get(GenTableDO, 201)
        assert row.remark == remark


async def test_generator_nonpaged_service_projects_the_same_read_model(test_db):
    document = json.loads((ROOT / 'valid/nested-list.json').read_text())
    test_db.add(GenTableDO(table_id=203, table_name='nonpage_note', table_comment='Nonpage', remark=document))
    await test_db.flush()
    service = GenTableService(GenTableRepository(test_db), AsyncMock(), test_db)
    records = await service.get_gen_table_list_services(GenTablePageQueryModel(), is_page=False)
    assert records[0].remark_text == '3. 第一\n  - 子项\n4. 第二'
    assert records[0].model_dump(by_alias=True)['remark'] == document
