from sqlalchemy.ext.asyncio import AsyncSession

from config.constant import CommonConstant
from config.error_codes import ErrorCode
from exceptions.exception import ResourceConflictException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.notice_do import NoticeDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.notice_vo import DeleteNoticeModel, NoticeModel, NoticePageQueryModel
from ports import INoticeRepository
from utils.common_util import CamelCaseUtil
from utils.transaction_manager import transactional


class NoticeService:
    """
    通知公告管理模块服务层
    """

    def __init__(self, notice_repo: INoticeRepository, query_db: AsyncSession):
        self.notice_repo = notice_repo
        self.query_db = query_db

    async def get_notice_list_services(self, query_object: NoticePageQueryModel, is_page: bool = True):
        """
        获取通知公告列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 通知公告列表信息对象
        """
        if is_page:
            notice_list_result = await self.notice_repo.paginate_with_filters(
                page=query_object.page,
                page_size=query_object.page_size,
                notice_title=query_object.notice_title,
                create_by=query_object.create_by,
                notice_type=query_object.notice_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
        else:
            notice_list_result = await self.notice_repo.paginate_with_filters(
                page=1,
                page_size=10000,
                notice_title=query_object.notice_title,
                create_by=query_object.create_by,
                notice_type=query_object.notice_type,
                begin_time=query_object.begin_time,
                end_time=query_object.end_time,
            )
            notice_list_result = notice_list_result.items if hasattr(notice_list_result, 'items') else notice_list_result

        return notice_list_result

    async def check_notice_unique_services(self, page_object: NoticeModel):
        """
        校验通知公告是否存在service

        :param page_object: 通知公告对象
        :return: 校验结果
        """
        notice_id = -1 if page_object.notice_id is None else page_object.notice_id
        notice = await self.notice_repo.find_by_content(
            notice_title=page_object.notice_title,
            notice_type=page_object.notice_type,
            notice_content=page_object.notice_content,
        )
        if notice and notice.notice_id != notice_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_notice_services(self, page_object: NoticeModel):
        """
        新增通知公告信息service

        :param page_object: 新增通知公告对象
        :return: 新增通知公告校验结果
        """
        if not await self.check_notice_unique_services(page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                user_message=f'新增通知公告{page_object.notice_title}失败，通知公告已存在',
            )

        db_notice = NoticeDO(**page_object.model_dump())
        add_result = await self.notice_repo.add(db_notice)
        return CrudResponseModel(is_success=True, message='新增成功', result={'noticeId': add_result.notice_id})

    @transactional()
    async def edit_notice_services(self, page_object: NoticeModel):
        """
        编辑通知公告信息service

        :param page_object: 编辑通知公告对象
        :return: 编辑通知公告校验结果
        """
        edit_notice = page_object.model_dump(exclude_unset=True)
        notice_info = await self.notice_detail_services(page_object.notice_id)
        if not notice_info.notice_id:
            raise ResourceNotFoundException(error_code=ErrorCode.RESOURCE_NOT_FOUND, user_message='通知公告不存在')

        if not await self.check_notice_unique_services(page_object):
            raise ResourceConflictException(
                error_code=ErrorCode.RESOURCE_CONFLICT,
                user_message=f'修改通知公告{page_object.notice_title}失败，通知公告已存在',
            )

        db_notice = await self.notice_repo.find_by_id(page_object.notice_id)
        if db_notice:
            for key, value in edit_notice.items():
                if hasattr(db_notice, key):
                    setattr(db_notice, key, value)
            await self.notice_repo.update(db_notice)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_notice_services(self, page_object: DeleteNoticeModel):
        """
        删除通知公告信息service

        :param page_object: 删除通知公告对象
        :return: 删除通知公告校验结果
        """
        if not page_object.notice_ids:
            raise ValidationException(
                error_code=ErrorCode.INVALID_INPUT,
                field='notice_ids',
                user_message='传入通知公告id为空',
            )

        notice_id_list = page_object.notice_ids.split(',')
        for notice_id in notice_id_list:
            await self.notice_repo.delete_by_id(int(notice_id))
        return CrudResponseModel(is_success=True, message='删除成功')

    async def notice_detail_services(self, notice_id: int):
        """
        获取通知公告详细信息service

        :param notice_id: 通知公告id
        :return: 通知公告id对应的信息
        """
        notice = await self.notice_repo.find_by_id(notice_id)
        if notice:
            result = NoticeModel(**CamelCaseUtil.transform_result(notice))
        else:
            result = NoticeModel(**{})

        return result
