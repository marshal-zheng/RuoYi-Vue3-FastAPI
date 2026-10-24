import { beforeEach, describe, expect, it, vi } from 'vitest';

const afterEachHandlers: Array<(to: { path: string }) => void> = [];
const dismissReloginPrompt = vi.fn();

vi.mock('@/router', () => ({
  default: {
    afterEach: (handler: (to: { path: string }) => void) => {
      afterEachHandlers.push(handler);
    },
  },
}));

vi.mock('@/utils/http', () => ({
  dismissReloginPrompt: (...args: unknown[]) => dismissReloginPrompt(...args),
}));

describe('auth feedback boundary', () => {
  beforeEach(async () => {
    afterEachHandlers.length = 0;
    dismissReloginPrompt.mockClear();
    vi.resetModules();
    await import('@/utils/auth-feedback-boundary');
  });

  it('dismisses leftover relogin prompts on login and register routes', () => {
    afterEachHandlers[0]({ path: '/login' });
    afterEachHandlers[0]({ path: '/register' });

    expect(dismissReloginPrompt).toHaveBeenCalledTimes(2);
  });

  it('keeps in-page relogin prompts on protected routes', () => {
    afterEachHandlers[0]({ path: '/index' });

    expect(dismissReloginPrompt).not.toHaveBeenCalled();
  });
});
