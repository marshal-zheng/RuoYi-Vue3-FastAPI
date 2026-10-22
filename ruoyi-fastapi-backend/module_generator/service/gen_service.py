"""
代码生成器服务层
提供代码生成业务表和字段的业务逻辑处理
"""

import io
import json
import os
import zipfile
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlglot import parse as sqlglot_parse
from sqlglot.errors import ParseError
from sqlglot.expressions import Create, Expression, Schema, Table

from config.constant import GenConstant
from config.env import DataBaseConfig, GenConfig
from config.error_codes import ErrorCode
from exceptions.exception import (
    ResourceConflictException,
    ResourceNotFoundException,
    ServiceException,
    ValidationException,
)
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_generator.entity.vo.gen_vo import (
    DeleteGenTableModel,
    EditGenTableModel,
    GenTableColumnModel,
    GenTableModel,
    GenTablePageQueryModel,
    GenTablePageReadModel,
    GenTableReadModel,
)
from module_generator.remark_policy import validate_remark_generation
from ports import IGenTableColumnRepository, IGenTableRepository
from utils.common_util import CamelCaseUtil
from utils.gen_util import GenUtils
from utils.template_util import TemplateInitializer, TemplateUtils
from utils.transaction_manager import transactional


class GenTableService:
    """
    代码生成业务表服务层
    """

    def __init__(
        self,
        table_repo: IGenTableRepository,
        column_repo: IGenTableColumnRepository,
        query_db: AsyncSession,
    ):
        self.table_repo = table_repo
        self.column_repo = column_repo
        self.query_db = query_db

    async def get_gen_table_list_services(self, query_object: GenTablePageQueryModel, is_page: bool = False):
        """
        获取代码生成业务表列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 代码生成业务列表信息对象
        """
        result = await self.table_repo.paginate_with_filters(
            page=query_object.page,
            page_size=query_object.page_size,
            table_name=query_object.table_name,
            table_comment=query_object.table_comment,
            begin_time=query_object.begin_time,
            end_time=query_object.end_time,
            is_page=is_page,
        )
        if is_page:
            return GenTablePageReadModel.model_validate(result)
        return [GenTableReadModel.model_validate(row) for row in result]

    async def get_gen_db_table_list_services(self, query_object: GenTablePageQueryModel, is_page: bool = False):
        """
        获取数据库列表信息service

        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 数据库列表信息对象
        """
        return await self.table_repo.get_db_table_list(
            page=query_object.page,
            page_size=query_object.page_size,
            table_name=query_object.table_name,
            table_comment=query_object.table_comment,
            begin_time=query_object.begin_time,
            end_time=query_object.end_time,
            is_page=is_page,
        )

    async def get_gen_db_table_list_by_name_services(self, table_names: list[str]):
        """
        根据表名称组获取数据库列表信息service

        :param table_names: 表名称组
        :return: 数据库列表信息对象
        """
        gen_db_table_list_result = await self.table_repo.get_db_tables_by_names(table_names)
        return [
            GenTableReadModel(**gen_table) for gen_table in CamelCaseUtil.transform_result(gen_db_table_list_result)
        ]

    @transactional()
    async def import_gen_table_services(self, gen_table_list: list[GenTableModel], current_user: CurrentUserModel):
        """
        导入表结构service

        :param gen_table_list: 导入表列表
        :param current_user: 当前用户信息对象
        :return: 导入结果
        """
        await self._import_tables_internal(gen_table_list, current_user)
        return CrudResponseModel(
            is_success=True,
            message='导入成功',
            result={
                'tableNames': [table.table_name for table in gen_table_list if table.table_name],
                'importedCount': len(gen_table_list),
            },
        )

    @transactional()
    async def edit_gen_table_services(self, page_object: EditGenTableModel):
        """
        编辑业务表信息service

        :param page_object: 编辑业务表对象
        :return: 编辑业务表校验结果
        """
        await self.get_gen_table_by_id_services(page_object.table_id)
        await self.validate_edit(page_object)

        edit_gen_table = page_object.model_dump(exclude_unset=True, by_alias=True)
        if 'params' in page_object.model_fields_set:
            edit_gen_table['options'] = json.dumps(edit_gen_table.get('params'))

        # 更新业务表
        await self.table_repo.update(edit_gen_table)

        # 更新字段信息
        for gen_table_column in page_object.columns:
            gen_table_column.update_by = page_object.update_by
            gen_table_column.update_time = datetime.now()
            await self.column_repo.update(gen_table_column.model_dump(by_alias=True))

        return CrudResponseModel(is_success=True, message='更新成功', result={'tableId': page_object.table_id})

    @transactional()
    async def delete_gen_table_services(self, page_object: DeleteGenTableModel):
        """
        删除业务表信息service

        :param page_object: 删除业务表对象
        :return: 删除业务表校验结果
        """
        if not page_object.table_ids:
            raise ServiceException(message='传入业务表id为空')

        table_id_list = [int(tid) for tid in page_object.table_ids.split(',') if tid]

        for table_id in table_id_list:
            # 先删除字段
            await self.column_repo.delete_by_table_id(table_id)
            # 再删除表
            await self.table_repo.delete_by_id(table_id)

        return CrudResponseModel(is_success=True, message='删除成功')

    async def get_gen_table_by_id_services(self, table_id: int):
        """
        获取需要生成的业务表详细信息service

        :param table_id: 需要生成的业务表id
        :return: 需要生成的业务表id对应的信息
        """
        gen_table = await self.table_repo.find_by_id(table_id)
        if not gen_table:
            raise ResourceNotFoundException(
                user_message='代码生成表不存在',
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                developer_message=f'table_id={table_id} not found',
            )
        result = await self.set_table_from_options(GenTableReadModel(**CamelCaseUtil.transform_result(gen_table)))
        return result

    async def get_gen_table_all_services(self):
        """
        获取所有业务表信息service

        :return: 所有业务表信息
        """
        gen_table_all = await self.table_repo.find_all()
        return [GenTableReadModel(**gen_table) for gen_table in CamelCaseUtil.transform_result(gen_table_all)]

    @transactional()
    async def create_table_services(self, sql: str, current_user: CurrentUserModel):
        """
        创建表结构service

        :param sql: 建表语句
        :param current_user: 当前用户信息对象
        :return: 创建表结构结果
        """
        try:
            sql_statements = sqlglot_parse(sql, dialect=DataBaseConfig.sqlglot_parse_dialect)
        except ParseError as exc:
            raise ValidationException(user_message='建表语句不合法', field='sql') from exc

        if not self._is_valid_create_table(sql_statements):
            raise ValidationException(user_message='仅支持完整的 CREATE TABLE 建表语句', field='sql')

        table_names = self._get_table_names(sql_statements)
        if len(set(table_names)) != len(table_names):
            raise ValidationException(user_message='建表语句包含重复表名', field='sql')
        if await self.get_gen_db_table_list_by_name_services(table_names):
            raise ResourceConflictException(user_message='待创建的表已存在，请使用导入功能')

        # 执行建表语句
        await self.table_repo.execute_sql_statements(sql_statements)

        # 导入表结构
        gen_table_list = await self.get_gen_db_table_list_by_name_services(table_names)
        await self._import_tables_internal(gen_table_list, current_user)

        return CrudResponseModel(
            is_success=True,
            message='创建表结构成功',
            result={'tableNames': table_names, 'createdCount': len(table_names)},
        )

    async def _import_tables_internal(self, gen_table_list: list[GenTableModel], current_user: CurrentUserModel):
        """
        内部方法：导入表结构（不创建新事务）
        """
        for table in gen_table_list:
            table_name = table.table_name
            GenUtils.init_table(table, current_user.user.user_name)

            add_gen_table = await self.table_repo.add(table.model_dump(by_alias=True))
            if add_gen_table:
                table.table_id = add_gen_table.table_id
                gen_table_columns = await self.column_repo.get_db_columns_by_table_name(table_name)
                for column_data in CamelCaseUtil.transform_result(gen_table_columns):
                    column = GenTableColumnModel(**column_data)
                    GenUtils.init_column_field(column, table)
                    await self.column_repo.add(column.model_dump(by_alias=True))

    @staticmethod
    def _is_valid_create_table(sql_statements: list[Expression]) -> bool:
        """
        校验sql语句是否为合法的建表语句

        :param sql_statements: sql语句的ast列表
        :return: 校验结果
        """
        return bool(sql_statements) and all(
            isinstance(statement, Create)
            and statement.kind == 'TABLE'
            and isinstance(statement.this, Schema)
            and isinstance(statement.this.this, Table)
            and not statement.this.this.db
            and not statement.this.this.catalog
            and bool(statement.this.expressions)
            and statement.expression is None
            and not statement.args.get('replace')
            for statement in sql_statements
        )

    @staticmethod
    def _get_table_names(sql_statements: list[Expression]) -> list[str]:
        """
        获取sql语句中所有的建表表名

        :param sql_statements: sql语句的ast列表
        :return: 建表表名列表
        """
        table_names = []
        for sql_statement in sql_statements:
            if isinstance(sql_statement, Create):
                table_names.append(sql_statement.find(Table).name)
        return table_names

    async def preview_code_services(self, table_id: int):
        """
        预览代码service

        :param table_id: 业务表id
        :return: 预览数据列表
        """
        gen_table_do = await self.table_repo.find_by_id(table_id)
        gen_table = GenTableModel(**CamelCaseUtil.transform_result(gen_table_do))

        await self.set_sub_table(gen_table)
        await self.set_pk_column(gen_table)
        await self._validate_remark_columns(gen_table)

        env = TemplateInitializer.init_jinja2()
        context = TemplateUtils.prepare_context(gen_table)
        template_list = TemplateUtils.get_template_list(gen_table.tpl_category, gen_table.tpl_web_type)

        preview_code_result = {}
        for template in template_list:
            render_content = env.get_template(template).render(**context)
            preview_code_result[template] = render_content

        return preview_code_result

    async def generate_code_services(self, table_name: str):
        """
        生成代码至指定路径service

        :param table_name: 业务表名称
        :return: 生成代码结果
        """
        env = TemplateInitializer.init_jinja2()
        render_info = await self._get_gen_render_info(table_name)

        for template in render_info[0]:
            render_content = env.get_template(template).render(**render_info[2])
            gen_path = self._get_gen_path(render_info[3], template)
            os.makedirs(os.path.dirname(gen_path), exist_ok=True)
            with open(gen_path, 'w', encoding='utf-8') as f:
                f.write(render_content)

        return CrudResponseModel(
            is_success=True,
            message='生成代码成功',
            result={'tableName': table_name, 'status': 'generated'},
        )

    async def batch_gen_code_services(self, table_names: list[str]):
        """
        批量生成代码service

        :param table_names: 业务表名称组
        :return: 下载代码结果
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table_name in table_names:
                env = TemplateInitializer.init_jinja2()
                render_info = await self._get_gen_render_info(table_name)
                for template_file, output_file in zip(render_info[0], render_info[1]):
                    render_content = env.get_template(template_file).render(**render_info[2])
                    zip_file.writestr(output_file, render_content)

        zip_data = zip_buffer.getvalue()
        zip_buffer.close()
        return zip_data

    async def _get_gen_render_info(self, table_name: str):
        """
        获取生成代码渲染模板相关信息

        :param table_name: 业务表名称
        :return: 生成代码渲染模板相关信息
        """
        gen_table_do = await self.table_repo.find_by_name(table_name)
        gen_table = GenTableModel(**CamelCaseUtil.transform_result(gen_table_do))

        await self.set_sub_table(gen_table)
        await self.set_pk_column(gen_table)
        await self._validate_remark_columns(gen_table)

        context = TemplateUtils.prepare_context(gen_table)
        template_list = TemplateUtils.get_template_list(gen_table.tpl_category, gen_table.tpl_web_type)
        output_files = [TemplateUtils.get_file_name(template, gen_table) for template in template_list]

        return [template_list, output_files, context, gen_table]

    @staticmethod
    def _get_gen_path(gen_table: GenTableModel, template: str) -> str:
        """
        根据GenTableModel对象和模板名称生成路径

        :param gen_table: GenTableModel对象
        :param template: 模板名称
        :return: 生成的路径
        """
        gen_path = gen_table.gen_path
        if gen_path == '/':
            return os.path.join(os.getcwd(), GenConfig.GEN_PATH, TemplateUtils.get_file_name(template, gen_table))
        return os.path.join(gen_path, TemplateUtils.get_file_name(template, gen_table))

    @transactional()
    async def sync_db_services(self, table_name: str):
        """
        同步数据库service

        :param table_name: 业务表名称
        :return: 同步数据库结果
        """
        gen_table_do = await self.table_repo.find_by_name(table_name)
        table = GenTableModel(**CamelCaseUtil.transform_result(gen_table_do))
        table_columns = table.columns
        table_column_map = {column.column_name: column for column in table_columns}

        # 获取数据库最新字段信息
        query_db_table_columns = await self.column_repo.get_db_columns_by_table_name(table_name)
        db_table_columns = [
            GenTableColumnModel(**column) for column in CamelCaseUtil.transform_result(query_db_table_columns)
        ]

        if not db_table_columns:
            raise ServiceException('同步数据失败，原表结构不存在')

        db_table_column_names = [column.column_name for column in db_table_columns]

        # 同步字段
        for column in db_table_columns:
            GenUtils.init_column_field(column, table)
            if column.column_name in table_column_map:
                prev_column = table_column_map[column.column_name]
                column.column_id = prev_column.column_id
                if column.list:
                    column.dict_type = prev_column.dict_type
                    column.query_type = prev_column.query_type
                if (
                    prev_column.is_required != ''
                    and not column.pk
                    and (column.insert or column.edit)
                    and (column.usable_column or column.super_column)
                ):
                    column.is_required = prev_column.is_required
                    column.html_type = prev_column.html_type
                await self.column_repo.update(column.model_dump(by_alias=True))
            else:
                await self.column_repo.add(column.model_dump(by_alias=True))

        # 删除已不存在的字段
        del_columns = [column for column in table_columns if column.column_name not in db_table_column_names]
        for column in del_columns:
            await self.column_repo.delete_by_column_id(column.column_id)

        return CrudResponseModel(
            is_success=True,
            message='同步成功',
            result={
                'tableId': table.table_id,
                'tableName': table_name,
            },
        )

    async def set_sub_table(self, gen_table: GenTableModel):
        """
        设置主子表信息

        :param gen_table: 业务表信息
        """
        if gen_table.sub_table_name:
            sub_table = await self.table_repo.find_by_name(gen_table.sub_table_name)
            gen_table.sub_table = GenTableModel(**CamelCaseUtil.transform_result(sub_table))

    async def set_pk_column(self, gen_table: GenTableModel):
        """
        设置主键列信息

        :param gen_table: 业务表信息
        """
        for column in gen_table.columns:
            if column.pk:
                gen_table.pk_column = column
                break

        if gen_table.pk_column is None and gen_table.columns:
            gen_table.pk_column = gen_table.columns[0]

        if gen_table.tpl_category == GenConstant.TPL_SUB and gen_table.sub_table:
            for column in gen_table.sub_table.columns:
                if column.pk:
                    gen_table.sub_table.pk_column = column
                    break
            if gen_table.sub_table.pk_column is None and gen_table.sub_table.columns:
                gen_table.sub_table.pk_column = gen_table.sub_table.columns[0]

    async def set_table_from_options(self, gen_table: GenTableModel):
        """
        设置代码生成其他选项值

        :param gen_table: 生成对象
        :return: 设置后的生成对象
        """
        params_obj = json.loads(gen_table.options) if gen_table.options else None
        if params_obj:
            gen_table.tree_code = params_obj.get(GenConstant.TREE_CODE)
            gen_table.tree_parent_code = params_obj.get(GenConstant.TREE_PARENT_CODE)
            gen_table.tree_name = params_obj.get(GenConstant.TREE_NAME)
            gen_table.parent_menu_id = params_obj.get(GenConstant.PARENT_MENU_ID)
            gen_table.parent_menu_name = params_obj.get(GenConstant.PARENT_MENU_NAME)

        return gen_table

    async def _validate_remark_columns(self, table):
        await self.set_table_from_options(table)
        validate_remark_generation(table)
        actual = {}
        for current in [table] + ([table.sub_table] if table.sub_table else []):
            if any(c.html_type == 'remark' for c in (current.columns or [])):
                rows = await self.column_repo.get_db_columns_by_table_name(current.table_name)
                actual[current.table_name] = {
                    row.column_name: dict(row._mapping) if hasattr(row, '_mapping') else vars(row) for row in rows
                }
        if actual:
            validate_remark_generation(table, actual)

    async def validate_edit(self, edit_gen_table: EditGenTableModel):
        """
        编辑保存参数校验

        :param edit_gen_table: 编辑业务表对象
        """
        await self.set_sub_table(edit_gen_table)
        if edit_gen_table.params is not None:
            edit_gen_table.options = json.dumps(edit_gen_table.params.model_dump(by_alias=True))
        await self.set_table_from_options(edit_gen_table)
        await self._validate_remark_columns(edit_gen_table)
        if edit_gen_table.tpl_category == GenConstant.TPL_TREE:
            params_obj = edit_gen_table.params.model_dump(by_alias=True)

            if GenConstant.TREE_CODE not in params_obj:
                raise ServiceException(message='树编码字段不能为空')
            if GenConstant.TREE_PARENT_CODE not in params_obj:
                raise ServiceException(message='树父编码字段不能为空')
            if GenConstant.TREE_NAME not in params_obj:
                raise ServiceException(message='树名称字段不能为空')

        if edit_gen_table.tpl_category == GenConstant.TPL_SUB:
            if not edit_gen_table.sub_table_name:
                raise ServiceException(message='关联子表的表名不能为空')
            if not edit_gen_table.sub_table_fk_name:
                raise ServiceException(message='子表关联的外键名不能为空')


class GenTableColumnService:
    """
    代码生成业务表字段服务层
    """

    def __init__(self, column_repo: IGenTableColumnRepository):
        self.column_repo = column_repo

    async def get_gen_table_column_list_by_table_id_services(self, table_id: int):
        """
        获取业务表字段列表信息service

        :param table_id: 业务表格id
        :return: 业务表字段列表信息对象
        """
        gen_table_column_list_result = await self.column_repo.find_by_table_id(table_id)
        return [
            GenTableColumnModel(**gen_table_column)
            for gen_table_column in CamelCaseUtil.transform_result(gen_table_column_list_result)
        ]
