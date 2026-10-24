import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  assertFeedbackRegistry,
  getFeedbackRegistry,
  resolveFeedbackRegistryEntry,
} from '@/utils/feedback/registry';

describe('feedback registry', () => {
  it('resolves known keys from the registry', () => {
    const registry = getFeedbackRegistry();

    expect(registry['system.user.create']).toEqual({ success: '新增用户成功' });
  });

  afterEach(() => vi.unstubAllEnvs());

  it.each([true, false])('rejects unregistered keys when DEV=%s', (isDev) => {
    vi.stubEnv('DEV', isDev);
    expect(() => resolveFeedbackRegistryEntry('missing.key')).toThrow(
      '[feedback] missing registry key: missing.key'
    );
  });

  it('rejects invalid registry entries during startup validation', () => {
    expect(() =>
      assertFeedbackRegistry({
        'broken.entry': undefined as unknown as { success: string },
      })
    ).toThrow('[feedback] invalid registry entry: broken.entry');
  });
});
