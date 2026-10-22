from io import BytesIO

from openpyxl import load_workbook

from utils.excel_util import ExcelUtil


def test_explicit_text_columns_are_literal_without_visible_prefix():
    for value in ['=1+1', '+SUM(A1)', '-1', '@x', '  中文\n\n😀']:
        data = ExcelUtil.export_list2excel([{'remark': value}], {'remark': '备注'}, text_columns={'remark'})
        cell = load_workbook(BytesIO(data), data_only=False).active['A2']
        assert cell.value == value
        assert cell.data_type == 's'
