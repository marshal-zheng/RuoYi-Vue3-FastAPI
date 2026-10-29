from ports import ICommonRepository


class CommonService:
    """
    通用模块服务层
    """

    def __init__(self, common_repo: ICommonRepository):
        self.common_repo = common_repo

    async def get_table_names_services(self) -> list[dict[str, str]]:
        """
        获取数据库中所有表名及其注释

        :return: 表名列表
        """
        return await self.common_repo.list_sys_tables()
