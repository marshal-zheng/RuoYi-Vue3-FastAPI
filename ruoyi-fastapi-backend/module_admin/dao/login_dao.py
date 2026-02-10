from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.user_do import UserDO


async def login_by_account(db: AsyncSession, user_name: str):
    """
    根据用户名查询用户信息

    :param db: orm对象
    :param user_name: 用户名
    :return: 用户对象
    """
    user = (
        await db.execute(
            select(UserDO, DeptDO)
            .where(UserDO.user_name == user_name, UserDO.del_flag == '0')
            .join(
                DeptDO,
                and_(UserDO.dept_id == DeptDO.dept_id, DeptDO.status == '0', DeptDO.del_flag == '0'),
                isouter=True,
            )
            .distinct()
        )
    ).first()

    return user
