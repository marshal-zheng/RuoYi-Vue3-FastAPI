import { describe, expect, it, vi } from 'vitest';

import {
  assertFeedbackRegistry,
  getFeedbackRegistry,
  resolveFeedbackRegistryEntryWithRuntime,
} from '@/utils/feedback/registry';

describe('feedback registry', () => {
  it('resolves known keys from the registry', () => {
    const registry = getFeedbackRegistry();

    expect(registry['system.user.create']).toEqual({ success: '新增用户成功' });
  });

  it('throws for missing keys in dev mode', () => {
    expect(() =>
      resolveFeedbackRegistryEntryWithRuntime('missing.key', {
        isDev: true,
        warn: vi.fn(),
        warnedKeys: new Set(),
      })
    ).toThrow('[feedback] missing registry key: missing.key');
  });

  it('warns once and falls back in prod mode', () => {
    const warn = vi.fn();
    const warnedKeys = new Set<string>();

    const first = resolveFeedbackRegistryEntryWithRuntime('missing.key', {
      isDev: false,
      warn,
      warnedKeys,
    });
    const second = resolveFeedbackRegistryEntryWithRuntime('missing.key', {
      isDev: false,
      warn,
      warnedKeys,
    });

    expect(first).toEqual({ success: '操作成功' });
    expect(second).toEqual({ success: '操作成功' });
    expect(warn).toHaveBeenCalledTimes(1);
  });

  it('rejects invalid registry entries during startup validation', () => {
    expect(() =>
      assertFeedbackRegistry({
        'broken.entry': undefined as unknown as { success: string },
      })
    ).toThrow('[feedback] invalid registry entry: broken.entry');
  });
});
