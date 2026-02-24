from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from config.constant import CommonConstant
from config.error_codes import ErrorCode
from exceptions.exception import ResourceConflictException, ResourceNotFoundException, ValidationException
from module_admin.entity.do.enums import StatusEnum
from module_admin.entity.do.post_do import PostDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.post_vo import DeletePostModel, PostModel, PostPageQueryModel
from ports import IPostRepository
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from utils.transaction_manager import transactional


class PostService:
    """
    岗位管理模块服务层
    """

    def __init__(self, post_repo: IPostRepository, query_db: AsyncSession):
        self.post_repo = post_repo
        self.query_db = query_db

    async def get_post_list_services(self, query_object: PostPageQueryModel, is_page: bool = False):
        """
        获取岗位列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 岗位列表信息对象
        """
        if is_page:
            post_list_result = await self.post_repo.paginate_with_filters(
                page=query_object.page_num,
                page_size=query_object.page_size,
                post_code=query_object.post_code,
                post_name=query_object.post_name,
                status=query_object.status,
            )
        else:
            post_list_result = await self.post_repo.find_all_with_filters(
                post_code=query_object.post_code,
                post_name=query_object.post_name,
                status=query_object.status,
            )

        return post_list_result

    async def check_post_name_unique_services(self, page_object: PostModel):
        """
        检查岗位名称是否唯一service

        :param page_object: 岗位对象
        :return: 校验结果
        """
        post_id = -1 if page_object.post_id is None else page_object.post_id
        post = await self.post_repo.find_by_name_or_code(post_name=page_object.post_name)
        if post and post.post_id != post_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    async def check_post_code_unique_services(self, page_object: PostModel):
        """
        检查岗位编码是否唯一service

        :param page_object: 岗位对象
        :return: 校验结果
        """
        post_id = -1 if page_object.post_id is None else page_object.post_id
        post = await self.post_repo.find_by_name_or_code(post_code=page_object.post_code)
        if post and post.post_id != post_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @transactional()
    async def add_post_services(self, page_object: PostModel):
        """
        新增岗位信息service

        :param page_object: 新增岗位对象
        :return: 新增岗位校验结果
        """
        if not await self.check_post_name_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增岗位{page_object.post_name}失败，岗位名称已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Post name already exists: post_name={page_object.post_name}',
            )
        if not await self.check_post_code_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'新增岗位{page_object.post_name}失败，岗位编码已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Post code already exists: post_code={page_object.post_code}',
            )

        db_post = PostDO(**page_object.model_dump())
        await self.post_repo.add(db_post)
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def edit_post_services(self, page_object: PostModel):
        """
        编辑岗位信息service

        :param page_object: 编辑岗位对象
        :return: 编辑岗位校验结果
        """
        edit_post = page_object.model_dump(exclude_unset=True)
        post_info = await self.post_detail_services(page_object.post_id)
        if not post_info.post_id:
            raise ResourceNotFoundException(
                user_message='岗位不存在',
                error_code=ErrorCode.ROLE_NOT_FOUND,
                developer_message=f'Post not found: post_id={page_object.post_id}',
            )

        if not await self.check_post_name_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'修改岗位{page_object.post_name}失败，岗位名称已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Post name already exists: post_name={page_object.post_name}',
            )
        if not await self.check_post_code_unique_services(page_object):
            raise ResourceConflictException(
                user_message=f'修改岗位{page_object.post_name}失败，岗位编码已存在',
                error_code=ErrorCode.ROLE_ALREADY_EXISTS,
                developer_message=f'Post code already exists: post_code={page_object.post_code}',
            )

        db_post = await self.post_repo.find_by_id(page_object.post_id)
        if db_post:
            for key, value in edit_post.items():
                if hasattr(db_post, key):
                    setattr(db_post, key, value)
            await self.post_repo.update(db_post)
        return CrudResponseModel(is_success=True, message='更新成功')

    @transactional()
    async def delete_post_services(self, page_object: DeletePostModel):
        """
        删除岗位信息service

        :param page_object: 删除岗位对象
        :return: 删除岗位校验结果
        """
        if not page_object.post_ids:
            raise ValidationException(
                user_message='传入岗位id为空',
                developer_message='Post IDs parameter is empty',
                field='post_ids',
            )

        post_id_list = page_object.post_ids.split(',')
        for post_id in post_id_list:
            post_id_value = int(post_id)
            post = await self.post_detail_services(post_id_value)
            if (await self.post_repo.count_users(post_id_value)) > 0:
                raise ResourceConflictException(
                    user_message=f'{post.post_name}已分配，不能删除',
                    error_code=ErrorCode.ROLE_IN_USE,
                    developer_message=f'Post is assigned to users: post_id={post_id_value}',
                )
            await self.post_repo.delete_by_id(post_id_value)
        return CrudResponseModel(is_success=True, message='删除成功')

    async def post_detail_services(self, post_id: int):
        """
        获取岗位详细信息service

        :param post_id: 岗位id
        :return: 岗位id对应的信息
        """
        post = await self.post_repo.find_by_id(post_id)
        if post:
            result = PostModel(**CamelCaseUtil.transform_result(post))
        else:
            result = PostModel(**{})

        return result

    @staticmethod
    async def export_post_list_services(post_list: List):
        """
        导出岗位信息service

        :param post_list: 岗位信息列表
        :return: 岗位信息对应excel的二进制数据
        """
        mapping_dict = {
            'postId': '岗位编号',
            'postCode': '岗位编码',
            'postName': '岗位名称',
            'postSort': '显示顺序',
            'status': '状态',
            'createBy': '创建者',
            'createTime': '创建时间',
            'updateBy': '更新者',
            'updateTime': '更新时间',
            'remark': '备注',
        }

        for item in post_list:
            if item.get('status') == StatusEnum.NORMAL.value:
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        binary_data = ExcelUtil.export_list2excel(post_list, mapping_dict)

        return binary_data
