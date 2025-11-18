import io
import uuid
from typing import Dict, List, Optional
import pandas as pd
from fastapi import UploadFile
from openpyxl import Workbook
from openpyxl.styles import Alignment, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions.exception import ServiceException
from module_admin.dao.protocol_dao import ProtocolDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel
)
from utils.common_util import CamelCaseUtil
from utils.page_util import PageResponseModel


HEADER_FIELDS = [
    ('sender', '发送方'),
    ('receiver', '接收方'),
    ('frequency', '传输频率'),
    ('baudRate', '传输速率(bps)'),
    ('method', '传输方式'),
    ('duration', '发送时长(ms)'),
    ('frameLength', '帧长度(Byte)'),
    ('errorHandling', '错误处理')
]

HEADER_NUMERIC_KEYS = {'baudRate', 'duration', 'frameLength'}
HEADER_SHEET_NAMES = ['报文配置', '报文头', 'header', '基础配置']

FIELD_COLUMNS = [
    {'key': 'field_name', 'label': '信息名称', 'width': 24},
    {'key': 'byte_count', 'label': '字节数', 'width': 12},
    {'key': 'byte_sequence', 'label': '字节序号', 'width': 14},
    {'key': 'value_range', 'label': '值域及含义', 'width': 32},
    {'key': 'unit', 'label': '量纲', 'width': 12},
    {'key': 'data_type', 'label': '数据类型', 'width': 14},
    {'key': 'scale', 'label': '比例尺', 'width': 12},
    {'key': 'remark', 'label': '备注', 'width': 24},
]

FIELD_SHEET_NAMES = ['字段列表', '字段定义', 'fields', '报文字段']

FIELD_COLUMN_ALIASES: Dict[str, List[str]] = {
    'field_code': ['字段标识', '字段ID', '字段编号', 'fieldCode', 'field_id'],
    'field_name': ['信息名称', '字段名称', 'name', 'fieldName'],
    'byte_count': ['字节数', 'byteCount'],
    'byte_sequence': ['字节序号', 'byteSequence'],
    'value_range': ['值域及含义', '值域', 'valueRange', 'meaning'],
    'unit': ['量纲', '单位', 'unit'],
    'data_type': ['数据类型', '类型', 'dataType'],
    'scale': ['比例尺', 'scale'],
    'parent_code': ['父级标识', '父级ID', 'parentId', 'parentCode'],
    'remark': ['备注', 'remark', 'note'],
}

DATA_TYPE_OPTIONS = ['UINT8', 'UINT16', 'UINT32', 'INT8', 'INT16', 'INT32', 'FLOAT', 'DOUBLE', 'STRING']
DATA_TYPE_ALIASES = {
    'uint8': 'UINT8', 'u8': 'UINT8', 'byte': 'UINT8', '无符号8位': 'UINT8',
    'uint16': 'UINT16', 'u16': 'UINT16',
    'uint32': 'UINT32', 'u32': 'UINT32',
    'int8': 'INT8', 'i8': 'INT8',
    'int16': 'INT16', 'i16': 'INT16',
    'int32': 'INT32', 'i32': 'INT32',
    'float': 'FLOAT', 'f32': 'FLOAT', '单精度': 'FLOAT',
    'double': 'DOUBLE', 'dbl': 'DOUBLE', 'f64': 'DOUBLE', '双精度': 'DOUBLE',
    'string': 'STRING', 'str': 'STRING', '文本': 'STRING', '字符串': 'STRING'
}

DEFAULT_HEADER_SAMPLE = {
    'sender': '设备A',
    'receiver': '地面站',
    'frequency': '单次',
    'baudRate': 115200,
    'method': '422',
    'duration': 1000,
    'frameLength': 128,
    'errorHandling': '重传'
}

DEFAULT_FIELD_SAMPLE = [
    {
        'field_name': '同步码1',
        'byte_count': 1,
        'byte_sequence': '0',
        'value_range': '0xEB',
        'unit': '',
        'data_type': 'UINT8',
        'scale': '1',
        'parent_code': '',
        'remark': ''
    },
    {
        'field_name': '同步码2',
        'byte_count': 1,
        'byte_sequence': '1',
        'value_range': '0x90',
        'unit': '',
        'data_type': 'UINT8',
        'scale': '1',
        'parent_code': '',
        'remark': ''
    },
    {
        'field_name': '报文字节数',
        'byte_count': 2,
        'byte_sequence': '2~3',
        'value_range': '0x0100',
        'unit': '',
        'data_type': 'UINT16',
        'scale': '1',
        'parent_code': '',
        'remark': ''
    }
]


class ProtocolService:
    """
    协议管理模块服务层
    """

    @classmethod
    async def get_protocol_list_services(
        cls, query_db: AsyncSession, query_object: ProtocolPageQueryModel, is_page: bool = False
    ):
        """
        获取协议列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 协议列表信息对象
        """
        protocol_list_result = await ProtocolDao.get_protocol_list(query_db, query_object, is_page)
        if is_page:
            return PageResponseModel(
                **{
                    **protocol_list_result.model_dump(),
                    'rows': CamelCaseUtil.transform_result(protocol_list_result.rows)
                }
            )
        else:
            return CamelCaseUtil.transform_result(protocol_list_result)

    @classmethod
    async def add_protocol_services(cls, query_db: AsyncSession, page_object: ProtocolModel):
        """
        新增协议信息service

        :param query_db: orm对象
        :param page_object: 新增协议对象
        :return: 新增协议校验结果
        """
        try:
            await ProtocolDao.add_protocol_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_protocol_services(cls, query_db: AsyncSession, page_object: ProtocolModel):
        """
        编辑协议信息service

        :param query_db: orm对象
        :param page_object: 编辑协议对象
        :return: 编辑协议校验结果
        """
        try:
            await ProtocolDao.edit_protocol_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_protocol_services(cls, query_db: AsyncSession, page_object: DeleteProtocolModel):
        """
        删除协议信息service

        :param query_db: orm对象
        :param page_object: 删除协议对象
        :return: 删除协议校验结果
        """
        try:
            await ProtocolDao.delete_protocol_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def protocol_detail_services(cls, query_db: AsyncSession, protocol_id: int):
        """
        获取协议详细信息service

        :param query_db: orm对象
        :param protocol_id: 协议ID
        :return: 协议ID对应的信息
        """
        protocol = await ProtocolDao.get_protocol_detail_by_id(query_db, protocol_id)
        if protocol:
            result = CamelCaseUtil.transform_result(protocol)
        else:
            result = CamelCaseUtil.transform_result({})

        return result

    @staticmethod
    async def get_protocol_import_template_services():
        """
        获取协议导入模板excel内容
        """
        workbook = Workbook()
        field_sheet = workbook.active
        field_sheet.title = '字段列表'
        header_fill = PatternFill(start_color='f2f2f2', end_color='f2f2f2', fill_type='solid')
        field_sheet.freeze_panes = 'A2'
        for column_index, column_meta in enumerate(FIELD_COLUMNS, start=1):
            cell = field_sheet.cell(row=1, column=column_index, value=column_meta['label'])
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = header_fill
            field_sheet.column_dimensions[get_column_letter(column_index)].width = column_meta['width']

        for row_index, row_data in enumerate(DEFAULT_FIELD_SAMPLE, start=2):
            for column_index, column_meta in enumerate(FIELD_COLUMNS, start=1):
                value = row_data.get(column_meta['key'], '')
                field_sheet.cell(row=row_index, column=column_index, value=value)

        data_type_column_index = next(
            (index for index, column_meta in enumerate(FIELD_COLUMNS, start=1) if column_meta['key'] == 'data_type'),
            None
        )
        if data_type_column_index:
            dv = DataValidation(
                type='list',
                formula1=f"\"{','.join(DATA_TYPE_OPTIONS)}\"",
                allow_blank=True,
                showErrorMessage=True,
            )
            data_type_column_letter = get_column_letter(data_type_column_index)
            dv.add(f'{data_type_column_letter}2:{data_type_column_letter}1048576')
            field_sheet.add_data_validation(dv)

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    async def protocol_import_preview_services(cls, file: UploadFile):
        """
        解析导入的协议配置文件
        """
        if not file or not file.filename:
            raise ServiceException(message='请选择要导入的文件')
        suffix = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if suffix not in ('xlsx', 'xls', 'csv'):
            raise ServiceException(message='仅支持 .xlsx/.xls/.csv 格式的文件')

        content = await file.read()
        if not content:
            raise ServiceException(message='文件内容为空')

        sheet_map = cls.__read_workbook(content, suffix)
        header = cls.__extract_header(sheet_map)
        fields = cls.__extract_fields(sheet_map)
        if not fields:
            raise ServiceException(message='文件中未解析到任何字段，请检查模板内容')
        return {'header': header, 'fields': fields}

    @staticmethod
    def __read_workbook(content: bytes, suffix: str):
        try:
            if suffix in ('xlsx', 'xls'):
                return pd.read_excel(io.BytesIO(content), sheet_name=None, dtype=str)
            text_io = io.StringIO(content.decode('utf-8-sig'))
            df = pd.read_csv(text_io, dtype=str)
            return {'字段列表': df}
        except Exception as exc:
            raise ServiceException(message=f'解析导入文件失败: {exc}') from exc

    @classmethod
    def __extract_header(cls, sheet_map: Dict[str, pd.DataFrame]):
        header_df: Optional[pd.DataFrame] = None
        for sheet_name in HEADER_SHEET_NAMES:
            if sheet_name in sheet_map:
                header_df = sheet_map[sheet_name]
                break
        if header_df is None:
            first_sheet = next(iter(sheet_map.values()))
            if set(first_sheet.columns).issuperset({label for _, label in HEADER_FIELDS}):
                header_df = first_sheet
        header_result = {
            key: (None if key in HEADER_NUMERIC_KEYS else '')
            for key, _ in HEADER_FIELDS
        }
        if header_df is None or header_df.empty:
            return header_result

        row_data = header_df.fillna('').iloc[0].to_dict()
        for key, label in HEADER_FIELDS:
            value = row_data.get(label, '')
            normalized = cls.__safe_number(value) if key in HEADER_NUMERIC_KEYS else str(value).strip()
            if normalized in (None, ''):
                header_result[key] = None if key in HEADER_NUMERIC_KEYS else ''
            else:
                header_result[key] = normalized
        return header_result

    @classmethod
    def __extract_fields(cls, sheet_map: Dict[str, pd.DataFrame]):
        fields_sheet: Optional[pd.DataFrame] = None
        for sheet_name in FIELD_SHEET_NAMES:
            if sheet_name in sheet_map:
                fields_sheet = sheet_map[sheet_name]
                break
        if fields_sheet is None:
            candidate = next(iter(sheet_map.values()))
            if any(header in candidate.columns for header in FIELD_COLUMN_ALIASES.get('field_name', [])):
                fields_sheet = candidate
        if fields_sheet is None:
            raise ServiceException(message='未找到包含字段定义的工作表，请确认模板未被修改')

        records = fields_sheet.fillna('').to_dict(orient='records')
        resolved_fields = []
        code_lookup: Dict[str, str] = {}
        name_lookup: Dict[str, str] = {}
        for index, row in enumerate(records):
            normalized = cls.__normalize_field_row(row, index, resolved_fields, code_lookup, name_lookup)
            if normalized:
                resolved_fields.append(normalized)

        return resolved_fields

    @classmethod
    def __normalize_field_row(cls, row: Dict, index: int, resolved_fields: List[Dict], code_lookup: Dict[str, str], name_lookup: Dict[str, str]):
        normalized_row = {str(k).strip(): row.get(k) for k in row.keys()}
        field_name = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('field_name', []))
        field_code = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('field_code', []))
        if not field_name and not field_code:
            return None

        unique_id = str(field_code).strip() if field_code else cls.__generate_field_id(index)
        unique_id = str(unique_id).strip() or cls.__generate_field_id(index)
        byte_count = cls.__to_int(cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('byte_count', [])), default=1)
        byte_sequence = cls.__format_sequence(cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('byte_sequence', [])))
        value_range = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('value_range', [])) or ''
        unit = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('unit', [])) or ''
        data_type_raw = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('data_type', []))
        scale = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('scale', [])) or '1'
        remark = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('remark', [])) or ''
        parent_ref = cls.__pick_value(normalized_row, FIELD_COLUMN_ALIASES.get('parent_code', []))
        parent_id = cls.__resolve_parent_id(parent_ref, resolved_fields, code_lookup, name_lookup)

        if field_name:
            name_lookup[str(field_name).strip()] = unique_id
        if field_code:
            code_lookup[str(field_code).strip()] = unique_id

        return {
            'id': unique_id,
            'parentId': parent_id,
            'fieldName': str(field_name).strip() if field_name else '',
            'byteCount': byte_count,
            'byteSequence': str(byte_sequence).strip(),
            'valueRange': str(value_range).strip(),
            'unit': str(unit).strip(),
            'dataType': cls.__normalize_data_type(data_type_raw),
            'scale': str(scale).strip() or '1',
            'remark': str(remark).strip()
        }

    @staticmethod
    def __pick_value(row: Dict, keys: List[str]):
        for key in keys:
            value = row.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text != '':
                return value
        return None

    @staticmethod
    def __generate_field_id(index: int):
        return f'field_{index}_{uuid.uuid4().hex}'

    @staticmethod
    def __normalize_data_type(value: Optional[str]):
        if not value:
            return 'STRING'
        value_str = str(value).strip()
        upper = value_str.upper()
        if upper in DATA_TYPE_OPTIONS:
            return upper
        return DATA_TYPE_ALIASES.get(value_str.lower(), 'STRING')

    @staticmethod
    def __safe_number(value: Optional[str]):
        if value is None:
            return None
        text = str(value).strip()
        if text == '':
            return None
        try:
            number = float(text)
            return int(number) if number.is_integer() else number
        except ValueError:
            return None

    @classmethod
    def __to_int(cls, value: Optional[str], default: int = 1):
        number = cls.__safe_number(value)
        return default if number is None else int(number)

    @classmethod
    def __resolve_parent_id(cls, parent_ref: Optional[str], resolved_fields: List[Dict], code_lookup: Dict[str, str], name_lookup: Dict[str, str]):
        if parent_ref is None:
            return None
        ref_text = str(parent_ref).strip()
        if not ref_text:
            return None
        if ref_text in code_lookup:
            return code_lookup[ref_text]
        if ref_text in name_lookup:
            return name_lookup[ref_text]
        if ref_text.isdigit():
            ref_index = int(ref_text)
            if 0 <= ref_index < len(resolved_fields):
                return resolved_fields[ref_index]['id']
            if 1 <= ref_index <= len(resolved_fields):
                return resolved_fields[ref_index - 1]['id']
        return None

    @classmethod
    def __format_sequence(cls, value: Optional[str]):
        if value is None:
            return ''
        number = cls.__safe_number(value)
        if number is None:
            return str(value).strip()
        if isinstance(number, float) and number.is_integer():
            return str(int(number))
        return str(number)
