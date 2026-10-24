import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getDicts } from './data';
import request from '@/utils/request';

vi.mock('@/utils/request', () => ({ default: vi.fn() }));

beforeEach(() => {
  vi.mocked(request).mockReset();
});

describe('dictionary transport', () => {
  it('forwards query cancellation and request options without an API cache', async () => {
    const signal = new AbortController().signal;
    const options = { retry: false as const, context: { owner: 'query' } };
    vi.mocked(request).mockResolvedValue({ items: [] });
    await getDicts('sys_yes_no', { signal, options });
    expect(request).toHaveBeenCalledWith(
      expect.objectContaining({ url: '/system/dict/data/type/sys_yes_no', signal }),
      options
    );
    await getDicts('sys_yes_no', { signal, options });
    expect(request).toHaveBeenCalledTimes(2);
  });

  it('preserves the original request rejection', async () => {
    const error = new Error('offline');
    vi.mocked(request).mockRejectedValue(error);
    await expect(getDicts('sys_yes_no')).rejects.toBe(error);
  });
});
