from sqlalchemy import desc, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.protocol_do import SysProtocol
from module_admin.entity.vo.protocol_vo import (
    ProtocolModel,
    ProtocolPageQueryModel,
    DeleteProtocolModel
)
from utils.page_util import PageUtil


class ProtocolDao:
    """
    协议管理模块数据库操作层
    """

    @classmethod
    async def get_protocol_detail_by_id(cls, db: AsyncSession, protocol_id: int):
        """
        根据协议ID获取协议详细信息

        :param db: orm对象
        :param protocol_id: 协议ID
        :return: 协议信息对象
        """
        protocol_info = (
            await db.execute(
                select(SysProtocol).where(
                    SysProtocol.protocol_id == protocol_id,
                    SysProtocol.del_flag == '0'
                )
            )
        ).scalars().first()

        return protocol_info

    @classmethod
    async def get_protocol_list(cls, db: AsyncSession, query_object: ProtocolPageQueryModel, is_page: bool = False):
        """
        根据查询参数获取协议列表信息

        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 协议列表信息对象
        """
        query = select(SysProtocol).where(
            SysProtocol.del_flag == '0'
        ).order_by(desc(SysProtocol.update_time))
        
        # 协议名称搜索
        if query_object.protocol_name:
            query = query.where(SysProtocol.protocol_name.like(f'%{query_object.protocol_name}%'))
        
        # 协议类型筛选
        if query_object.protocol_type:
            query = query.where(SysProtocol.protocol_type == query_object.protocol_type)
        
        # 日期范围筛选
        if query_object.begin_time and query_object.end_time:
            query = query.where(
                SysProtocol.create_time.between(query_object.begin_time, query_object.end_time)
            )
        
        if is_page:
            return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, True)
        else:
            protocol_list = (await db.execute(query)).scalars().all()
            return protocol_list

    @classmethod
    async def add_protocol_dao(cls, db: AsyncSession, protocol: ProtocolModel):
        """
        新增协议数据库操作

        :param db: orm对象
        :param protocol: 协议对象
        :return: 新增的协议对象
        """
        db_protocol = SysProtocol(**protocol.model_dump(exclude_unset=True))
        db.add(db_protocol)
        await db.flush()
        return db_protocol

    @classmethod
    async def edit_protocol_dao(cls, db: AsyncSession, protocol: ProtocolModel):
        """
        编辑协议数据库操作

        :param db: orm对象
        :param protocol: 需要更新的协议对象
        :return: None
        """
        await db.execute(
            update(SysProtocol)
            .where(SysProtocol.protocol_id == protocol.protocol_id)
            .values(**protocol.model_dump(exclude_unset=True, exclude={'protocol_id'}))
        )

    @classmethod
    async def delete_protocol_dao(cls, db: AsyncSession, protocol: DeleteProtocolModel):
        """
        删除协议数据库操作

        :param db: orm对象
        :param protocol: 删除协议对象
        :return: None
        """
        protocol_id_list = protocol.protocol_ids.split(',')
        await db.execute(
            update(SysProtocol)
            .where(SysProtocol.protocol_id.in_(protocol_id_list))
            .values(
                del_flag='2',
                update_by=protocol.update_by,
                update_time=protocol.update_time
            )
        )
