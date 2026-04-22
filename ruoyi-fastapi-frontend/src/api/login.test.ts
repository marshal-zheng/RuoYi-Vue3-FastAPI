import { beforeEach, describe, expect, it, vi } from 'vitest';

const requestMock = vi.fn();

vi.mock('@/utils/request', () => ({
  default: (...args: unknown[]) => requestMock(...args),
}));

describe('login api', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('serializes login payload as x-www-form-urlencoded data', async () => {
    requestMock.mockResolvedValue({ token: 'demo-token-admin' });

    const { login } = await import('./login');
    await login('admin', 'admin123', '1234', 'uuid-1');

    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/login',
        method: 'post',
        headers: expect.objectContaining({
          'Content-Type': 'application/x-www-form-urlencoded',
        }),
        data: expect.any(URLSearchParams),
      })
    );

    const config = requestMock.mock.calls[0][0] as { data: URLSearchParams };
    expect(config.data.toString()).toBe('username=admin&password=admin123&code=1234&uuid=uuid-1');
  });
});
