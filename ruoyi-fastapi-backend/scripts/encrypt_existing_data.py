#!/usr/bin/env python3
"""加密现有的明文敏感数据"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from config.database import AsyncSessionLocal
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_do import SysUser
from utils.log_util import logger
from utils.sensitive import SensitiveDataCipher


async def encrypt_user_data(session) -> dict:
    """加密用户表的敏感数据"""
    result = await session.execute(select(SysUser))
    users = result.scalars().all()
    
    counts = {'phonenumber': 0, 'email': 0, 'id_card': 0}
    
    for user in users:
        # 加密手机号
        phone = getattr(user, 'phonenumber', None)
        if phone and not phone.startswith('enc:v1:'):
            encrypted = SensitiveDataCipher.encrypt(phone)
            user.phonenumber = encrypted
            user.phonenumber_hash = SensitiveDataCipher.hash(phone)
            counts['phonenumber'] += 1
        
        # 加密邮箱
        email = getattr(user, 'email', None)
        if email and not email.startswith('enc:v1:'):
            encrypted = SensitiveDataCipher.encrypt(email)
            user.email = encrypted
            user.email_hash = SensitiveDataCipher.hash(email)
            counts['email'] += 1
        
        # 加密身份证号
        id_card = getattr(user, 'id_card', None)
        if id_card and not id_card.startswith('enc:v1:'):
            encrypted = SensitiveDataCipher.encrypt(id_card)
            user.id_card = encrypted
            user.id_card_hash = SensitiveDataCipher.hash(id_card)
            counts['id_card'] += 1
    
    return counts


async def encrypt_dept_data(session) -> int:
    """加密部门表的敏感数据"""
    result = await session.execute(select(SysDept))
    depts = result.scalars().all()
    
    updated = 0
    for dept in depts:
        phone = getattr(dept, 'phone', None)
        if phone and phone != '' and not phone.startswith('enc:v1:'):
            encrypted = SensitiveDataCipher.encrypt(phone)
            dept.phone = encrypted
            dept.phone_hash = SensitiveDataCipher.hash(phone)
            updated += 1
    
    return updated


async def main() -> None:
    logger.info('开始加密现有明文敏感数据...')
    
    # 初始化加密器
    SensitiveDataCipher._ensure_ready()
    
    async with AsyncSessionLocal() as session:
        user_counts = await encrypt_user_data(session)
        dept_count = await encrypt_dept_data(session)
        await session.commit()
    
    logger.info(
        f'敏感数据加密完成: '
        f'用户手机号={user_counts["phonenumber"]}, '
        f'用户邮箱={user_counts["email"]}, '
        f'用户身份证={user_counts["id_card"]}, '
        f'部门电话={dept_count}'
    )


if __name__ == '__main__':
    asyncio.run(main())
