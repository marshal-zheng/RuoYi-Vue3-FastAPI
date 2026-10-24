"""Account isolation and project-role authorization for shared scene layouts."""

import re

from exceptions.exception import PermissionException, ValidationException


class DashboardService:
    def __init__(self, repository, project_detail):
        self.repository = repository
        self.project_detail = project_detail

    async def account_id(self, scope, key, current_user, *, write=False):
        if current_user.user is None or not current_user.user.user_id:
            raise PermissionException(user_message='请先登录')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', key):
            raise ValidationException(user_message='无效的仪表盘标识')
        if scope == 'account':
            return current_user.user.user_id
        if scope != 'scene' or not key.isdecimal() or int(key) <= 0 or str(int(key)) != key:
            raise ValidationException(user_message='场景必须绑定有效工程编号')
        permissions = {'project:project:query'}
        if write:
            permissions.add('project:project:edit')
        if not permissions.issubset(current_user.permissions) and '*:*:*' not in current_user.permissions:
            raise PermissionException(user_message='没有场景仪表盘权限')
        await self.project_detail(int(key))
        return 0

    async def load(self, scope, key, user):
        account = await self.account_id(scope, key, user)
        return self.repository.snapshot(await self.repository.load(scope, key, account))

    async def save(self, scope, key, user, request):
        account = await self.account_id(scope, key, user, write=True)
        return await self.repository.save(
            scope,
            key,
            account,
            user.user.user_id,
            request.document,
            request.expected_revision,
        )

    async def remove(self, scope, key, user, expected_revision):
        account = await self.account_id(scope, key, user, write=True)
        await self.repository.remove(scope, key, account, expected_revision)
