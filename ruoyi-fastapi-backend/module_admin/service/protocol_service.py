from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.dao.protocol_dao import ProtocolDao
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel
)
from utils.common_util import CamelCaseUtil
from utils.page_util import PageResponseModel


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
