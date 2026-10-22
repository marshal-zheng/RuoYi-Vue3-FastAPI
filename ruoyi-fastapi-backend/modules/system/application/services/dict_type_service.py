"""Dictionary type application service."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from modules.system.application.read_models.dict_read_models import DictTypeDetailReadModel

if TYPE_CHECKING:
    from module_admin.entity.vo.dict_vo import DeleteDictTypeModel, DictTypeModel, DictTypePageQueryModel
    from ports import IDictDataRepository, IDictDataService, IDictTypeRepository, IRedisClient

from common.remark_document_v1 import remark_display_text
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from config.error_codes import ErrorCode
from exceptions.exception import ResourceConflictException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.dict_do import DictTypeDO
from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class DictTypeService:
    """
    字典类型管理模块服务层
    """

    def __init__(
        self,
        dict_type_repo: IDictTypeRepository,
        dict_data_repo: IDictDataRepository,
        dict_data_service: IDictDataService,
    ):
        self.dict_type_repo = dict_type_repo
        self.dict_data_repo = dict_data_repo
        self.dict_data_service = dict_data_service

    async def get_dict_type_list_services(self, query_object: DictTypePageQueryModel, is_page: bool = False):
        """
        获取字典类型列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典类型列表信息对象
        """
        if is_page:
            dict_type_list_result = await self.dict_type_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                dict_name=query_object.dict_name,
                dict_type=query_object.dict_type,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
        else:
            dict_type_list_result = await self.dict_type_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                dict_name=query_object.dict_name,
                dict_type=query_object.dict_type,
                status=query_object.status,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
            if hasattr(dict_type_list_result, 'items'):
                dict_type_list_result = dict_type_list_result.items

        return dict_type_list_result

    async def check_dict_type_unique_services(self, page_object: DictTypeModel):
        """
        校验字典类型称是否唯一service

        :param page_object: 字典类型对象
        :return: 校验结果
        """
        dict_id = -1 if page_object.dict_id is None else page_object.dict_id
        dict_type = await self.dict_type_repo.find_by_type(page_object.dict_type)
        if dict_type and dict_type.dict_id != dict_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_dict_type_services(
        self,
        redis: IRedisClient,
        page_object: DictTypeModel,
        operator: str | None = None,
    ):
        """
        新增字典类型信息service

        :param redis: redis对象
        :param page_object: 新增岗位对象
        :return: 新增字典类型校验结果
        """
        if operator:
            page_object.create_by = operator
            page_object.create_time = datetime.now()
            page_object.update_by = operator
            page_object.update_time = datetime.now()

        if not await self.check_dict_type_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增字典{page_object.dict_name}失败，字典类型已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Dict type already exists: dict_type={page_object.dict_type}',
            )

        db_dict_type = DictTypeDO(**page_object.model_dump())
        add_result = await self.dict_type_repo.add(db_dict_type)
        await redis.set(f'{RedisInitKeyConfig.SYS_DICT.key}:{page_object.dict_type}', '')
        return CrudResponseModel(is_success=True, message='新增成功', result={'dictId': add_result.dict_id})

    @transactional()
    async def edit_dict_type_services(
        self,
        redis: IRedisClient,
        page_object: DictTypeModel,
        operator: str | None = None,
    ):
        """
        编辑字典类型信息service

        :param redis: redis对象
        :param page_object: 编辑字典类型对象
        :return: 编辑字典类型校验结果
        """
        if operator:
            page_object.update_by = operator
            page_object.update_time = datetime.now()
        edit_dict_type = page_object.model_dump(exclude_unset=True)
        dict_type_info = await self.dict_type_detail_services(page_object.dict_id)

        if not await self.check_dict_type_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'修改字典{page_object.dict_name}失败，字典类型已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Dict type already exists: dict_type={page_object.dict_type}',
            )

        if dict_type_info.dict_type != page_object.dict_type:
            dict_data_list = await self.dict_data_repo.find_all(filters={'dict_type': dict_type_info.dict_type})
            for dict_data in dict_data_list:
                dict_data.dict_type = page_object.dict_type
                dict_data.update_by = page_object.update_by
                dict_data.update_time = page_object.update_time
                await self.dict_data_repo.update(dict_data)

        db_dict_type = await self.dict_type_repo.find_by_id(page_object.dict_id)
        if db_dict_type:
            for key, value in edit_dict_type.items():
                if hasattr(db_dict_type, key):
                    setattr(db_dict_type, key, value)
            await self.dict_type_repo.update(db_dict_type)

        cache_keys = [
            f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type}'
            for dict_type in dict.fromkeys((dict_type_info.dict_type, page_object.dict_type))
        ]
        await redis.delete(*cache_keys)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_dict_type_services(self, redis: IRedisClient, page_object: DeleteDictTypeModel):
        """
        删除字典类型信息service

        :param redis: redis对象
        :param page_object: 删除字典类型对象
        :return: 删除字典类型校验结果
        """
        if not page_object.dict_ids:
            raise ValidationException(
                user_message='传入字典类型id为空',
                developer_message='Dict type IDs parameter is empty',
                field='dict_ids',
            )

        dict_id_list = page_object.dict_ids.split(',')
        delete_dict_type_list = []
        for dict_id in dict_id_list:
            dict_type_info = await self.dict_type_detail_services(int(dict_id))
            if (await self.dict_data_repo.count_by_type(dict_type_info.dict_type)) > 0:
                raise ResourceConflictException(
                    user_message=f'{dict_type_info.dict_name}已分配，不能删除',
                    error_code=ErrorCode.DICT_TYPE_EXISTS,
                    developer_message=f'Dict type is in use: dict_type={dict_type_info.dict_type}',
                )
            await self.dict_type_repo.delete_by_id(int(dict_id))
            delete_dict_type_list.append(f'{RedisInitKeyConfig.SYS_DICT.key}:{dict_type_info.dict_type}')
        if delete_dict_type_list:
            await redis.delete(*delete_dict_type_list)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def dict_type_detail_services(self, dict_id: int):
        """
        获取字典类型详细信息service

        :param dict_id: 字典类型id
        :return: 字典类型id对应的信息
        """
        dict_type = await self.dict_type_repo.find_by_id(dict_id)
        if dict_type:
            result = DictTypeDetailReadModel(**CamelCaseUtil.transform_result(dict_type))
        else:
            raise ResourceNotFoundException(
                user_message='字典类型不存在',
                error_code=ErrorCode.DICT_NOT_FOUND,
                developer_message=f'dict_id={dict_id} not found',
            )

        return result

    async def export_dict_type_list_services(self, dict_type_list: list):
        """
        导出字典类型信息service

        :param dict_type_list: 字典信息列表
        :return: 字典信息对应excel的二进制数据
        """
        mapping_dict = {
            'dictId': '字典编号',
            'dictName': '字典名称',
            'dictType': '字典类型',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in dict_type_list:
            if item.get('status') == StatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        binary_data = ExcelUtil.export_list2excel(
            [{**item, 'remark': remark_display_text(item.get('remark'))} for item in dict_type_list],
            mapping_dict,
            text_columns={'remark'},
        )

        return binary_data

    async def refresh_sys_dict_services(self, redis: IRedisClient):
        """
        刷新字典缓存信息service

        :param redis: redis对象
        :return: 刷新字典缓存校验结果
        """
        await self.dict_data_service.init_cache_sys_dict_services(redis)
        result = dict(is_success=True, message='刷新成功')
        return CrudResponseModel(**result)
