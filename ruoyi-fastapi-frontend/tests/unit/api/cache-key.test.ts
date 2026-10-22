import { expect, it, vi } from 'vitest';
import { clearCacheKey } from '@/api/monitor/cache';

const request = vi.hoisted(() => vi.fn().mockResolvedValue(null));
vi.mock('@/utils/request', () => ({ default: request }));

it('sends the namespace and full literal key instead of a matching suffix', async () => {
  await clearCacheKey('sys_config', 'own:nested[*]');
  expect(request).toHaveBeenCalledWith(
    expect.objectContaining({
      url: '/monitor/cache/clearCacheKey/sys_config%3Aown%3Anested%5B*%5D',
      method: 'delete',
    })
  );
});
