from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from module_admin.entity.do.datasource_do import DataSourceDO
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.datasource_vo import DataSourceModel, DataSourceQueryModel, TestConnectionModel
from module_admin.service.datasource_connector import test_connection
from ports import IDataSourceRepository
from utils.transaction_manager import transactional


class DataSourceService:
    def __init__(self, datasource_repo: IDataSourceRepository, query_db: AsyncSession):
        self.datasource_repo = datasource_repo
        self.query_db = query_db

    async def get_datasource_list_services(self, query: DataSourceQueryModel):
        items, total = await self.datasource_repo.paginate_with_filters(
            page=query.page_num,
            page_size=query.page_size,
            name=query.name,
            type=query.type,
            status=query.status,
        )
        rows = []
        for item in items:
            row = DataSourceModel.model_validate(item).model_dump()
            row['password'] = ''
            rows.append(row)
        return {'rows': rows, 'total': total}

    async def datasource_detail_services(self, datasource_id: int):
        ds = await self.datasource_repo.get_by_id(datasource_id)
        if not ds:
            raise HTTPException(status_code=404, detail='数据源不存在')
        result = DataSourceModel.model_validate(ds).model_dump()
        result['password'] = ''
        return result

    @transactional()
    async def add_datasource_services(self, data: DataSourceModel, current_user: str):
        existing = await self.datasource_repo.find_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail=f"数据源名称'{data.name}'已存在")
        ds = DataSourceDO(
            name=data.name,
            type=data.type,
            host=data.host,
            port=data.port,
            username=data.username,
            password=data.password or '',
            database_name=data.database_name,
            description=data.description,
            status='offline',
            extra_config=data.extra_config or {},
            create_by=current_user,
            create_time=datetime.now(),
        )
        await self.datasource_repo.add(ds)
        return CrudResponseModel(is_success=True, message='新增成功')

    @transactional()
    async def edit_datasource_services(self, data: DataSourceModel, current_user: str):
        existing = await self.datasource_repo.get_by_id(data.id)
        if not existing:
            raise HTTPException(status_code=404, detail='数据源不存在')
        name_check = await self.datasource_repo.find_by_name(data.name)
        if name_check and name_check.id != data.id:
            raise HTTPException(status_code=400, detail=f"数据源名称'{data.name}'已存在")
        existing.name = data.name
        existing.host = data.host
        existing.port = data.port
        existing.username = data.username
        if data.password:
            existing.password = data.password
        existing.database_name = data.database_name
        existing.description = data.description
        existing.extra_config = data.extra_config or {}
        existing.update_by = current_user
        existing.update_time = datetime.now()
        await self.datasource_repo.update(existing)
        return CrudResponseModel(is_success=True, message='修改成功')

    @transactional()
    async def delete_datasource_services(self, datasource_ids: str):
        id_list = [int(i) for i in datasource_ids.split(',') if i.strip()]
        count = await self.datasource_repo.soft_delete_by_ids(id_list)
        return CrudResponseModel(is_success=True, message=f'删除成功，共删除{count}条记录')

    async def test_connection_services(self, config: TestConnectionModel):
        result = await test_connection(
            type=config.type,
            host=config.host,
            port=config.port,
            username=config.username or '',
            password=config.password or '',
            database_name=config.database_name or '',
            extra_config=config.extra_config or {},
        )
        return result

    async def test_saved_connection_services(self, datasource_id: int):
        ds = await self.datasource_repo.get_by_id(datasource_id)
        if not ds:
            raise HTTPException(status_code=404, detail='数据源不存在')
        result = await test_connection(
            type=ds.type,
            host=ds.host,
            port=ds.port,
            username=ds.username or '',
            password=ds.password or '',
            database_name=ds.database_name or '',
            extra_config=ds.extra_config or {},
        )
        ds.status = 'online' if result.success else 'offline'
        ds.update_time = datetime.now()
        await self.datasource_repo.update(ds)
        await self.query_db.commit()
        return result
