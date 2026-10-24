"""Dictionary data application service."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from config.error_codes import ErrorCode
from exceptions.exception import ResourceConflictException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.dict_do import DictDataDO
from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.dict_vo import DeleteDictDataModel, DictDataModel, DictDataPageQueryModel
from ports import IDictDataRepository, IDictTypeRepository, IRedisClient
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class DictDataService:
    """
    字典数据管理模块服务层
    """

    def __init__(
        self,
        dict_type_repo: IDictTypeRepository,
        dict_data_repo: IDictDataRepository,
    ):
        self.dict_type_repo = dict_type_repo
        self.dict_data_repo = dict_data_repo

    async def get_dict_data_list_services(self, query_object: DictDataPageQueryModel, is_page: bool = False):
        """
        获取字典数据列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典数据列表信息对象
        """
        if is_page:
            dict_data_list_result = await self.dict_data_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                dict_type=query_object.dict_type,
                dict_label=query_object.dict_label,
                status=query_object.status,
            )
        else:
            dict_data_list_result = await self.dict_data_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                dict_type=query_object.dict_type,
                dict_label=query_object.dict_label,
                status=query_object.status,
            )
            if hasattr(dict_data_list_result, 'items'):
                dict_data_list_result = dict_data_list_result.items

        return dict_data_list_result

    async def query_dict_data_list_services(self, dict_type: str):
        """
        获取字典数据列表信息service

        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        return await self.dict_data_repo.find_by_type(dict_type)

    async def init_cache_sys_dict_services(self, redis: IRedisClient):
        """
        应用初始化：获取所有字典类型对应的字典数据信息并缓存service

        :param redis: redis对象
        :return:
        """
        keys = await redis.keys(f'{RedisInitKeyConfig.SYS_DICT.key}:*')
        if keys:
            await redis.delete(*keys)
        dict_type_all = await self.dict_type_repo.find_all()
        for dict_type_obj in [item for item in dict_type_all if item.status == StatusEnum.NORMAL.value]:
            dict_type = dict_type_obj.dict_type
            dict_data_list = await self.dict_data_repo.find_by_type(dict_type)
            dict_data = [CamelCaseUtil.transform_result(row) for row in dict_data_list if row]
            await redis.set(
                f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}',
                json.dumps(dict_data, ensure_ascii=False, default=str),
            )

    async def query_dict_data_list_from_cache_services(self, redis: IRedisClient, dict_type: str):
        """
        从缓存获取字典数据列表信息service

        :param redis: redis对象
        :param dict_type: 字典类型
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        cache_key = f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}'
        dict_data_list_result = await redis.get(cache_key)
        if dict_data_list_result:
            return json.loads(dict_data_list_result)

        return await self._load_dict_data_and_refresh_cache(redis, dict_type, cache_key)

    async def _load_dict_data_and_refresh_cache(self, redis: IRedisClient, dict_type: str, cache_key: str):
        """
        当缓存未命中时，从数据库加载字典数据并写回缓存
        """
        dict_data_list = await self.dict_data_repo.find_by_type(dict_type)
        dict_data = [CamelCaseUtil.transform_result(row) for row in dict_data_list if row]
        await redis.set(cache_key, json.dumps(dict_data, ensure_ascii=False, default=str))
        return dict_data

    async def check_dict_data_unique_services(self, page_object: DictDataModel):
        """
        校验字典数据是否唯一service

        :param page_object: 字典数据对象
        :return: 校验结果
        """
        dict_code = -1 if page_object.dict_code is None else page_object.dict_code
        dict_data = await self.dict_data_repo.find_by_type_and_label(page_object.dict_type, page_object.dict_label)
        if dict_data and dict_data.dict_code != dict_code:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_dict_data_services(
        self,
        redis: IRedisClient,
        page_object: DictDataModel,
        operator: Optional[str] = None,
    ):
        """
        新增字典数据信息service

        :param redis: redis对象
        :param page_object: 新增岗位对象
        :return: 新增字典数据校验结果
        """
        if operator:
            page_object.create_by = operator
            page_object.create_time = datetime.now()
            page_object.update_by = operator
            page_object.update_time = datetime.now()
        if not await self.check_dict_data_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增字典数据{page_object.dict_label}失败，{page_object.dict_type}下已存在该字典数据',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=(
                    f'Dict data already exists: dict_type={page_object.dict_type}, '
                    f'dict_label={page_object.dict_label}'
                ),
            )

        db_dict_data = DictDataDO(**page_object.model_dump())
        add_result = await self.dict_data_repo.add(db_dict_data)
        dict_data_list = await self.query_dict_data_list_services(page_object.dict_type)
        await redis.set(
            f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}',
            json.dumps(CamelCaseUtil.transform_result(dict_data_list), ensure_ascii=False, default=str),
        )
        return CrudResponseModel(is_success=True, message='新增成功', result={'dictCode': add_result.dict_code})

    @transactional()
    async def edit_dict_data_services(
        self,
        redis: IRedisClient,
        page_object: DictDataModel,
        operator: Optional[str] = None,
    ):
        """
        编辑字典数据信息service

        :param redis: redis对象
        :param page_object: 编辑字典数据对象
        :return: 编辑字典数据校验结果
        """
        if operator:
            page_object.update_by = operator
            page_object.update_time = datetime.now()
        edit_data_type = page_object.model_dump(exclude_unset=True)
        dict_data_info = await self.dict_data_detail_services(page_object.dict_code)

        if not await self.check_dict_data_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增字典数据{page_object.dict_label}失败，{page_object.dict_type}下已存在该字典数据',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=(
                    f'Dict data already exists: dict_type={page_object.dict_type}, '
                    f'dict_label={page_object.dict_label}'
                ),
            )

        db_dict_data = await self.dict_data_repo.find_by_code(page_object.dict_code)
        if db_dict_data:
            for key, value in edit_data_type.items():
                if hasattr(db_dict_data, key):
                    setattr(db_dict_data, key, value)
            await self.dict_data_repo.update(db_dict_data)
        for dict_type in dict.fromkeys((dict_data_info.dict_type, page_object.dict_type)):
            await self._load_dict_data_and_refresh_cache(
                redis, dict_type, f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}'
            )
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_dict_data_services(self, redis: IRedisClient, page_object: DeleteDictDataModel):
        """
        删除字典数据信息service

        :param redis: redis对象
        :param page_object: 删除字典数据对象
        :return: 删除字典数据校验结果
        """
        if not page_object.dict_codes:
            raise ValidationException(
                user_message='传入字典数据id为空',
                developer_message='Dict data codes parameter is empty',
                field='dict_codes',
            )

        dict_code_list = page_object.dict_codes.split(',')
        delete_dict_type_list = []
        for dict_code in dict_code_list:
            dict_data = await self.dict_data_detail_services(int(dict_code))
            await self.dict_data_repo.delete_by_code(int(dict_code))
            delete_dict_type_list.append(dict_data.dict_type)
        for dict_type in list(set(delete_dict_type_list)):
            dict_data_list = await self.query_dict_data_list_services(dict_type)
            await redis.set(
                f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}',
                json.dumps(CamelCaseUtil.transform_result(dict_data_list), ensure_ascii=False, default=str),
            )
        return CrudResponseModel(is_success=True, message='删除成功')

    async def dict_data_detail_services(self, dict_code: int):
        """
        获取字典数据详细信息service

        :param dict_code: 字典数据id
        :return: 字典数据id对应的信息
        """
        dict_data = await self.dict_data_repo.find_by_code(dict_code)
        if dict_data:
            result = DictDataModel(**CamelCaseUtil.transform_result(dict_data))
        else:
            raise ResourceNotFoundException(
                user_message='字典数据不存在',
                error_code=ErrorCode.DICT_NOT_FOUND,
                developer_message=f'dict_code={dict_code} not found',
            )

        return result

    async def export_dict_data_list_services(self, dict_data_list: list):
        """
        导出字典数据信息service

        :param dict_data_list: 字典数据信息列表
        :return: 字典数据信息对应excel的二进制数据
        """
        mapping_dict = {
            'dictCode': '字典编码',
            'dictSort': '字典标签',
            'dictLabel': '字典键值',
            'dictValue': '字典排序',
            'dictType': '字典类型',
            'cssClass': '样式属性',
            'listClass': '表格回显样式',
            'isDefault': '是否默认',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in dict_data_list:
            if item.get('status') == StatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('isDefault') == 'Y':
                item['isDefault'] = '是'
            else:
                item['isDefault'] = '否'
        binary_data = ExcelUtil.export_list2excel(dict_data_list, mapping_dict)

        return binary_data
