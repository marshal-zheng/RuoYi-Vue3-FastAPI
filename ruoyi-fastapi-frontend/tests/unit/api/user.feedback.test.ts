import { beforeEach, expect, it, vi } from 'vitest';
import { addUser, updateUser } from '@/api/system/user';
const request = vi.hoisted(() => vi.fn());
vi.mock('@/utils/request', () => ({ default: request }));
const authority = { data: { userId: 42, nickName: 'User' }, postIds: [3], roleIds: [2] };
beforeEach(() => request.mockReset().mockResolvedValue(authority));
it.each(['create', 'update'] as const)(
  'preserves nested %s authority, scope and success feedback while the owner handles errors',
  async (operation) => {
    const options = { context: { 'ruoyi.query-scope': '1:test' } };
    const result =
      operation === 'create'
        ? await addUser(
            { userName: 'created_user', nickName: 'User', password: 'Secret123' },
            options,
            { silentError: true }
          )
        : await updateUser({ userId: 42, nickName: 'User' }, options, { silentError: true });
    expect(result).toBe(authority);
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/system/user',
        method: operation === 'create' ? 'post' : 'put',
        silentError: true,
        feedback: { mode: 'auto', key: `system.user.${operation}` },
      }),
      options
    );
  }
);
