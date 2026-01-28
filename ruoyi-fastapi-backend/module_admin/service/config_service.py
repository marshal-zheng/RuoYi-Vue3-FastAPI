from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from exceptions.exception import (
    ResourceNotFoundException,
    ResourceConflictException,
    ValidationException
)
from config.error_codes import ErrorCode
from module_admin.entity.do.config_do import SysConfig
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel, DeleteConfigModel
from module_admin.repository import ConfigRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class ConfigService:
    """
    参数配置管理模块服务层
    """

    @classmethod
    async def get_config_list_services(
        cls, query_db: AsyncSession, query_object: ConfigPageQueryModel, is_page: bool = False
    ):
        """
        获取参数配置列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 参数配置列表信息对象
        """
        config_repo = ConfigRepository(query_db)
        if is_page:
            config_list_result = await config_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                config_name=query_object.config_name,
                config_key=query_object.config_key,
                config_type=query_object.config_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time
            )
        else:
            config_list_result = await config_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                config_name=query_object.config_name,
                config_key=query_object.config_key,
                config_type=query_object.config_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time
            )
            config_list_result = config_list_result.rows if hasattr(config_list_result, 'rows') else config_list_result

        return config_list_result

    @classmethod
    async def init_cache_sys_config_services(cls, query_db: AsyncSession, redis):
        """
        应用初始化：获取所有参数配置对应的键值对信息并缓存service

        :param query_db: orm对象
        :param redis: redis对象
        :return:
        """
        # 获取以sys_config:开头的键列表
        keys = await redis.keys(f'{RedisInitKeyConfig.SYS_CONFIG.key}:*')
        # 删除匹配的键
        if keys:
            await redis.delete(*keys)
        config_repo = ConfigRepository(query_db)
        config_all_result = await config_repo.paginate_with_filters(page=1, page_size=10000)
        config_all = config_all_result.rows if hasattr(config_all_result, 'rows') else config_all_result
        for config_obj in config_all:
            await redis.set(
                f"{RedisInitKeyConfig.SYS_CONFIG.key}:{config_obj.get('configKey')}",
                config_obj.get('configValue'),
            )

    @classmethod
    async def query_config_list_from_cache_services(cls, redis, config_key: str):
        """
        从缓存获取参数键名对应值service

        :param redis: redis对象
        :param config_key: 参数键名
        :return: 参数键名对应值
        """
        result = await redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_key}')

        return result

    @classmethod
    async def check_config_key_unique_services(cls, query_db: AsyncSession, page_object: ConfigModel):
        """
        校验参数键名是否唯一service

        :param query_db: orm对象
        :param page_object: 参数配置对象
        :return: 校验结果
        """
        config_id = -1 if page_object.config_id is None else page_object.config_id
        config_repo = ConfigRepository(query_db)
        config = await config_repo.find_by_key(page_object.config_key)
        if config and config.config_id != config_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    @transactional()
    async def add_config_services(cls, request: Request, query_db: AsyncSession, page_object: ConfigModel):
        """
        新增参数配置信息service

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增参数配置对象
        :return: 新增参数配置校验结果
        """
        if not await cls.check_config_key_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'新增参数{page_object.config_name}失败，参数键名已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Config key already exists: config_key={page_object.config_key}'
            )
        
        config_repo = ConfigRepository(query_db)
        db_config = SysConfig(**page_object.model_dump())
        await config_repo.add(db_config)
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.SYS_CONFIG.key}:{page_object.config_key}', page_object.config_value
        )
        return CrudResponseModel(is_success=True, message='新增成功')

    @classmethod
    @transactional()
    async def edit_config_services(cls, request: Request, query_db: AsyncSession, page_object: ConfigModel):
        """
        编辑参数配置信息service

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 编辑参数配置对象
        :return: 编辑参数配置校验结果
        """
        edit_config = page_object.model_dump(exclude_unset=True)
        config_info = await cls.config_detail_services(query_db, page_object.config_id)
        if not config_info.config_id:
            raise ResourceNotFoundException(
                user_message='参数配置不存在',
                error_code=ErrorCode.DICT_NOT_FOUND,
                developer_message=f'Config not found: config_id={page_object.config_id}'
            )
        
        if not await cls.check_config_key_unique_services(query_db, page_object):
            raise ResourceConflictException(
                user_message=f'修改参数{page_object.config_name}失败，参数键名已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Config key already exists: config_key={page_object.config_key}'
            )
        
        config_repo = ConfigRepository(query_db)
        config = await config_repo.find_by_id(page_object.config_id)
        if config:
            for key, value in edit_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            await config_repo.update(config)
        if config_info.config_key != page_object.config_key:
            await request.app.state.redis.delete(
                f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_info.config_key}'
            )
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.SYS_CONFIG.key}:{page_object.config_key}', page_object.config_value
        )
        return CrudResponseModel(is_success=True, message='更新成功')

    @classmethod
    @transactional()
    async def delete_config_services(cls, request: Request, query_db: AsyncSession, page_object: DeleteConfigModel):
        """
        删除参数配置信息service

        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 删除参数配置对象
        :return: 删除参数配置校验结果
        """
        if not page_object.config_ids:
            raise ValidationException(
                user_message='传入参数配置id为空',
                developer_message='Config IDs parameter is empty',
                field='config_ids'
            )
        
        config_id_list = page_object.config_ids.split(',')
        delete_config_key_list = []
        config_repo = ConfigRepository(query_db)
        for config_id in config_id_list:
            config_info = await cls.config_detail_services(query_db, int(config_id))
            if config_info.config_type == CommonConstant.YES:
                raise ValidationException(
                    user_message=f'内置参数{config_info.config_key}不能删除',
                    developer_message=f'Built-in config cannot be deleted: config_key={config_info.config_key}',
                    field='config_type'
                )
            else:
                await config_repo.delete_by_id(int(config_id))
                delete_config_key_list.append(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_info.config_key}')
        if delete_config_key_list:
            await request.app.state.redis.delete(*delete_config_key_list)
        return CrudResponseModel(is_success=True, message='删除成功')

    @classmethod
    async def config_detail_services(cls, query_db: AsyncSession, config_id: int):
        """
        获取参数配置详细信息service

        :param query_db: orm对象
        :param config_id: 参数配置id
        :return: 参数配置id对应的信息
        """
        config_repo = ConfigRepository(query_db)
        config = await config_repo.find_by_id(config_id)
        if config:
            result = ConfigModel(**CamelCaseUtil.transform_result(config))
        else:
            result = ConfigModel(**dict())

        return result

    @staticmethod
    async def export_config_list_services(config_list: List):
        """
        导出参数配置信息service

        :param config_list: 参数配置信息列表
        :return: 参数配置信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            'configId': '参数主键',
            'configName': '参数名称',
            'configKey': '参数键名',
            'configValue': '参数键值',
            'configType': '系统内置',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in config_list:
            if item.get('configType') == 'Y':
                item['configType'] = '是'
            else:
                item['configType'] = '否'
        binary_data = ExcelUtil.export_list2excel(config_list, mapping_dict)

        return binary_data

    @classmethod
    async def refresh_sys_config_services(cls, request: Request, query_db: AsyncSession):
        """
        刷新字典缓存信息service

        :param request: Request对象
        :param query_db: orm对象
        :return: 刷新字典缓存校验结果
        """
        await cls.init_cache_sys_config_services(query_db, request.app.state.redis)

        return CrudResponseModel(is_success=True, message='刷新成功')
