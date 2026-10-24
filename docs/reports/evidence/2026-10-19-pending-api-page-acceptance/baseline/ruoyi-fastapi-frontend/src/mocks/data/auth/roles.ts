import type { MockRole } from '../types';
import { MOCK_ROLE_IDS, MOCK_STATUS } from '../_shared';

export const mockRoles = [
  {
    roleId: MOCK_ROLE_IDS.admin,
    roleKey: 'admin',
    roleName: '超级管理员',
    status: MOCK_STATUS.normal,
    permissions: ['*:*:*'],
  },
  {
    roleId: MOCK_ROLE_IDS.editor,
    roleKey: 'editor',
    roleName: '编辑员',
    status: MOCK_STATUS.normal,
    permissions: ['system:user:query', 'system:user:add', 'system:user:edit'],
  },
] satisfies MockRole[];
