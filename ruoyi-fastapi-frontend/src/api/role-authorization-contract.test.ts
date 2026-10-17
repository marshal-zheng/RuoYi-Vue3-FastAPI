import { beforeEach, expect, it, vi } from 'vitest';
import { updateAuthRole } from './system/user';
import { authUserCancel, authUserCancelAll, authUserSelectAll } from './system/role';

const send = vi.hoisted(() => vi.fn().mockResolvedValue(null));
vi.mock('@/utils/request', () => ({ default: send }));
beforeEach(() => send.mockClear());

it.each([
  [updateAuthRole, '/system/user/authRole', { userId: 42, roleIds: [] }],
  [authUserSelectAll, '/system/role/authUser/selectAll', { roleId: 20, userIds: [42, 43] }],
  [authUserCancel, '/system/role/authUser/cancel', { roleId: 20, userId: 42 }],
  [authUserCancelAll, '/system/role/authUser/cancelAll', { roleId: 20, userIds: [42, 43] }],
] as const)('authorization mutation uses typed JSON: %s', async (call, url, payload) => {
  await (call as (data: unknown) => Promise<unknown>)(payload);
  expect(send.mock.calls[0][0]).toMatchObject({ url, method: 'put', data: payload });
  expect(send.mock.calls[0][0]).not.toHaveProperty('params');
  expect(send.mock.calls[0][0].feedback.mode).toBe('auto');
});
