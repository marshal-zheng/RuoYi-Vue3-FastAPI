import type { MockAccount } from '../types';
import { MOCK_STATUS, MOCK_USER_IDS } from '../_shared';

export const mockAccounts = [
  {
    username: 'admin',
    password: 'admin123',
    userId: MOCK_USER_IDS.admin,
    displayName: '若依',
    introduction: 'I am a super administrator',
    avatar: '',
    roles: ['admin'],
    permissions: ['*:*:*'],
    status: MOCK_STATUS.normal,
  },
  {
    username: 'editor',
    password: 'editor123',
    userId: MOCK_USER_IDS.editor,
    displayName: '编辑员',
    introduction: 'I am an editor',
    avatar: '',
    roles: ['editor'],
    permissions: ['system:user:query', 'system:user:add', 'system:user:edit'],
    status: MOCK_STATUS.normal,
  },
] satisfies MockAccount[];
