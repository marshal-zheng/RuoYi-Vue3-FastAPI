from sqlalchemy.ext.asyncio import AsyncSession

from common.remark_document_v1 import remark_display_text
from config.constant import CommonConstant
from config.enums import RedisInitKeyConfig
from config.error_codes import ErrorCode
from exceptions.exception import (
    BusinessException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.config_vo import ConfigModel, ConfigPageQueryModel, DeleteConfigModel
from modules.system.application.read_models.config_read_models import ConfigDetailReadModel
from modules.system.infrastructure.config_repository import ConfigRepository  # noqa: F401 - test patch target
from ports import IConfigRepository, IRedisClient
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class ConfigService:
    """
    参数配置管理模块服务层
    """

    def __init__(self, config_repo: IConfigRepository, query_db: AsyncSession):
        self.query_db = query_db
        self.config_repo = config_repo

    async def get_config_list_services(self, query_object: ConfigPageQueryModel, is_page: bool = False):
        """
        获取参数配置列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 参数配置列表信息对象
        """
        if is_page:
            config_list_result = await self.config_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                config_name=query_object.config_name,
                config_key=query_object.config_key,
                config_type=query_object.config_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
        else:
            config_list_result = await self.config_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                config_name=query_object.config_name,
                config_key=query_object.config_key,
                config_type=query_object.config_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
            config_list_result = (
                config_list_result.items if hasattr(config_list_result, 'items') else config_list_result
            )

        return config_list_result

    async def init_cache_sys_config_services(self, redis: IRedisClient):
        """
        应用初始化：获取所有参数配置对应的键值对信息并缓存service

        :param redis: redis对象
        :return:
        """
        # 获取以sys_config:开头的键列表
        keys = await redis.keys(f'{RedisInitKeyConfig.SYS_CONFIG.key}:*')
        # 删除匹配的键
        if keys:
            await redis.delete(*keys)
        config_all_result = await self.config_repo.paginate_with_filters(page=1, page_size=10000)
        config_all = config_all_result.items if hasattr(config_all_result, 'items') else config_all_result
        for config_obj in config_all:
            await redis.set(
                f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_obj.get("configKey")}',
                config_obj.get('configValue'),
            )

    async def query_config_list_from_cache_services(self, redis: IRedisClient, config_key: str):
        """
        从缓存获取参数键名对应值service

        :param redis: redis对象
        :param config_key: 参数键名
        :return: 参数键名对应值
        """
        result = await redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_key}')

        return result

    async def check_config_key_unique_services(self, page_object: ConfigModel):
        """
        校验参数键名是否唯一service

        :param page_object: 参数配置对象
        :return: 校验结果
        """
        config_id = -1 if page_object.config_id is None else page_object.config_id
        config = await self.config_repo.find_by_key(page_object.config_key)
        if config and config.config_id != config_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_config_services(self, redis: IRedisClient, page_object: ConfigModel):
        """
        新增参数配置信息service

        :param redis: redis对象
        :param page_object: 新增参数配置对象
        :return: 新增参数配置校验结果
        """
        if not await self.check_config_key_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增参数{page_object.config_name}失败，参数键名已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Config key already exists: config_key={page_object.config_key}',
            )

        db_config = ConfigDO(**page_object.model_dump())
        add_result = await self.config_repo.add(db_config)
        await redis.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{page_object.config_key}', page_object.config_value)
        return CrudResponseModel(is_success=True, message='新增成功', result={'configId': add_result.config_id})

    @transactional()
    async def edit_config_services(self, redis: IRedisClient, page_object: ConfigModel):
        """
        编辑参数配置信息service

        :param redis: redis对象
        :param page_object: 编辑参数配置对象
        :return: 编辑参数配置校验结果
        """
        edit_config = page_object.model_dump(exclude_unset=True)
        config_info = await self.config_detail_services(page_object.config_id)

        if not await self.check_config_key_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'修改参数{page_object.config_name}失败，参数键名已存在',
                error_code=ErrorCode.DICT_TYPE_EXISTS,
                developer_message=f'Config key already exists: config_key={page_object.config_key}',
            )

        config = await self.config_repo.find_by_id(page_object.config_id)
        if config:
            for key, value in edit_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            await self.config_repo.update(config)
        if config_info.config_key != page_object.config_key:
            await redis.delete(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_info.config_key}')
        await redis.set(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{page_object.config_key}', page_object.config_value)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_config_services(self, redis: IRedisClient, page_object: DeleteConfigModel):
        """
        删除参数配置信息service

        :param redis: redis对象
        :param page_object: 删除参数配置对象
        :return: 删除参数配置校验结果
        """
        if not page_object.config_ids:
            raise ValidationException(
                user_message='传入参数配置id为空', developer_message='Config IDs parameter is empty', field='config_ids'
            )

        config_id_list = page_object.config_ids.split(',')
        delete_config_key_list = []
        for config_id in config_id_list:
            config_info = await self.config_detail_services(int(config_id))
            if config_info.config_type == CommonConstant.YES:
                raise BusinessException(
                    user_message=f'内置参数【{config_info.config_key}】不能删除',
                    error_code=ErrorCode.CONFIG_BUILTIN_CANNOT_DELETE,
                    http_status=409,
                    developer_message=f'Built-in config cannot be deleted: config_key={config_info.config_key}, config_id={config_id}',
                )
            else:
                await self.config_repo.delete_by_id(int(config_id))
                delete_config_key_list.append(f'{RedisInitKeyConfig.SYS_CONFIG.key}:{config_info.config_key}')
        if delete_config_key_list:
            await redis.delete(*delete_config_key_list)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def config_detail_services(self, config_id: int):
        """
        获取参数配置详细信息service

        :param config_id: 参数配置id
        :return: 参数配置id对应的信息
        """
        config = await self.config_repo.find_by_id(config_id)
        if config:
            result = ConfigDetailReadModel(**CamelCaseUtil.transform_result(config))
        else:
            raise ResourceNotFoundException(
                user_message='参数配置不存在',
                error_code=ErrorCode.CONFIG_NOT_FOUND,
                developer_message=f'config_id={config_id} not found',
            )

        return result

    @staticmethod
    async def export_config_list_services(config_list: list):
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
        binary_data = ExcelUtil.export_list2excel(
            [{**item, 'remark': remark_display_text(item.get('remark'))} for item in config_list],
            mapping_dict,
            text_columns={'remark'},
        )

        return binary_data

    async def refresh_sys_config_services(self, redis: IRedisClient):
        """
        刷新字典缓存信息service

        :param redis: redis对象
        :return: 刷新字典缓存校验结果
        """
        await self.init_cache_sys_config_services(redis)

        return CrudResponseModel(is_success=True, message='刷新成功')
