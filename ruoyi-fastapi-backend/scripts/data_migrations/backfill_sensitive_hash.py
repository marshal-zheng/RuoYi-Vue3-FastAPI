from sqlalchemy import select

from config.database import AsyncSessionLocal
from module_admin.entity.do.dept_do import DeptDO
from module_admin.entity.do.user_do import UserDO
from utils.log_util import logger
from utils.sensitive import SensitiveDataCipher


async def _backfill_user_hashes(session) -> dict:
    result = await session.execute(select(UserDO))
    users = result.scalars().all()
    counts = {
        'phonenumber': 0,
        'email': 0,
        'id_card': 0,
    }
    for user in users:
        phone = getattr(user, 'phonenumber', None)
        if phone and not getattr(user, 'phonenumber_hash', None):
            user.phonenumber_hash = SensitiveDataCipher.hash(phone)
            counts['phonenumber'] += 1

        email = getattr(user, 'email', None)
        if email and not getattr(user, 'email_hash', None):
            user.email_hash = SensitiveDataCipher.hash(email)
            counts['email'] += 1

        id_card = getattr(user, 'id_card', None)
        if id_card and not getattr(user, 'id_card_hash', None):
            user.id_card_hash = SensitiveDataCipher.hash(id_card)
            counts['id_card'] += 1

    return counts


async def _backfill_dept_phone_hash(session) -> int:
    result = await session.execute(select(DeptDO))
    depts = result.scalars().all()
    updated = 0
    for dept in depts:
        phone = getattr(dept, 'phone', None)
        if phone is None or phone == '':
            continue
        current_hash = getattr(dept, 'phone_hash', None)
        if current_hash:
            continue
        dept.phone_hash = SensitiveDataCipher.hash(phone)
        updated += 1
    return updated


async def migrate() -> None:
    logger.info('Backfilling sensitive hash columns...')
    async with AsyncSessionLocal() as session:
        user_counts = await _backfill_user_hashes(session)
        updated_depts = await _backfill_dept_phone_hash(session)
        await session.commit()
    logger.info(
        'Sensitive hash backfill complete. phones=%s, emails=%s, id_cards=%s, depts=%s',
        user_counts['phonenumber'],
        user_counts['email'],
        user_counts['id_card'],
        updated_depts,
    )
