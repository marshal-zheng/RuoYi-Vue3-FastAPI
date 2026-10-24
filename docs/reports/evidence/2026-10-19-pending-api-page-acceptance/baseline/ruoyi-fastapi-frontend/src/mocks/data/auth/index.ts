import type { AuthMockData } from '../types';
import { mockAccounts } from './accounts';
import { mockRoles } from './roles';

export const authMockData = {
  accounts: mockAccounts,
  roles: mockRoles,
} satisfies AuthMockData;

export * from './accounts';
export * from './roles';
