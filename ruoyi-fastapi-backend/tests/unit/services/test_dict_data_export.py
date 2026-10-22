from io import BytesIO

import pytest
from openpyxl import load_workbook

from modules.system.application.services.dict_data_service import DictDataService


@pytest.mark.asyncio
async def test_export_headers_match_distinct_sort_label_and_value():
    service = DictDataService(dict_type_repo=None, dict_data_repo=None)
    content = await service.export_dict_data_list_services(
        [
            {
                'dictCode': 208,
                'dictSort': 7,
                'dictLabel': '显示标签',
                'dictValue': 'stored_value',
                'dictType': 'qa_export',
                'status': '0',
                'isDefault': 'N',
            },
        ]
    )
    rows = list(load_workbook(BytesIO(content), read_only=True).active.values)
    data = dict(zip(rows[0], rows[1], strict=True))
    assert data['字典编码'] == 208
    assert data['字典排序'] == 7
    assert data['字典标签'] == '显示标签'
    assert data['字典键值'] == 'stored_value'
    assert data['状态'] == '正常'
