import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import useSettingsStore from '@/store/modules/settings';
import {
  bindZxThemePreferenceUpdater,
  projectZxThemeScope,
  setZxThemePreference,
  zxThemeConfig,
  zxThemePreference,
} from './zx-theme-config';

let unbind: (() => void) | null = null;

beforeEach(async () => {
  unbind = bindZxThemePreferenceUpdater(async () => true);
  setActivePinia(createPinia());
  await setZxThemePreference({
    themeId: 'default',
    mode: 'light',
    density: 'default',
  });
  document.documentElement.removeAttribute('data-zx-theme');
  document.documentElement.removeAttribute('data-zx-variant');
  document.documentElement.classList.remove('dark');
});

afterEach(() => {
  unbind?.();
  unbind = null;
});

describe('theme preference ownership', () => {
  it('shares the committed preference between selector, Settings and Provider without reading DOM', async () => {
    const settings = useSettingsStore();
    document.documentElement.classList.add('dark');
    expect(settings.isDark).toBe(false);
    settings.toggleTheme();
    await setZxThemePreference({ themeId: 'factory-blue', density: 'compact' });
    expect(zxThemePreference.value).toEqual({
      themeId: 'factory-blue',
      mode: 'dark',
      density: 'compact',
    });
    expect(settings.isDark).toBe(true);
    expect(zxThemeConfig.value.portalTarget()).toBe(document.body);
    expect(zxThemeConfig.value.themeId).toBe('factory-blue');
    expect(document.documentElement.dataset.zxTheme).toBeUndefined();
    expect(JSON.parse(localStorage.getItem('zx-theme-preference')!)).toEqual(
      zxThemePreference.value
    );
  });

  it('projects the committed variant without changing the requested preference', () => {
    projectZxThemeScope({
      themeId: 'tech-blue',
      variantKey: 'library-resolved-variant',
      selection: { mode: 'dark' },
    });
    expect(document.documentElement.dataset.zxVariant).toBe('library-resolved-variant');
    expect(zxThemePreference.value.mode).toBe('light');
  });

  it('rejects unsupported preferences instead of writing an unavailable theme', () => {
    expect(() => setZxThemePreference({ themeId: 'missing' })).toThrow(
      'Invalid ZXUI theme preference'
    );
    expect(zxThemePreference.value.themeId).toBe('default');
  });

  it('keeps the last committed density and stored choice when the scope rejects an update', async () => {
    unbind?.();
    const issue = vi.fn();
    unbind = bindZxThemePreferenceUpdater(async () => false, issue);
    await setZxThemePreference({ density: 'compact' });
    expect(zxThemePreference.value.density).toBe('default');
    expect(zxThemeConfig.value.density).toBe('default');
    expect(JSON.parse(localStorage.getItem('zx-theme-preference')!).density).toBe('default');
    expect(issue).toHaveBeenCalledWith('update-failed');
  });

  it('persists only the latest density after a slower earlier request completes', async () => {
    unbind?.();
    let finishFirst!: () => void;
    let startFirst!: () => void;
    const firstGate = new Promise<void>((resolve) => {
      finishFirst = resolve;
    });
    const firstStarted = new Promise<void>((resolve) => {
      startFirst = resolve;
    });
    const applied: string[] = [];
    unbind = bindZxThemePreferenceUpdater(async (next) => {
      applied.push(next.density);
      if (next.density === 'compact') {
        startFirst();
        await firstGate;
      }
      return true;
    });

    const first = setZxThemePreference({ density: 'compact' });
    await firstStarted;
    const latest = setZxThemePreference({ density: 'comfortable' });
    finishFirst();
    await Promise.all([first, latest]);

    expect(applied).toEqual(['compact', 'comfortable']);
    expect(zxThemePreference.value.density).toBe('comfortable');
    expect(JSON.parse(localStorage.getItem('zx-theme-preference')!).density).toBe('comfortable');
  });

  it('keeps a successful density change when local storage rejects the write', async () => {
    unbind?.();
    const issue = vi.fn();
    unbind = bindZxThemePreferenceUpdater(async () => true, issue);
    const stored = localStorage.getItem('zx-theme-preference');
    const denied = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage denied');
    });
    try {
      await setZxThemePreference({ density: 'compact' });
      expect(zxThemePreference.value.density).toBe('compact');
      expect(localStorage.getItem('zx-theme-preference')).toBe(stored);
      expect(issue).toHaveBeenCalledWith('storage-unavailable');
    } finally {
      denied.mockRestore();
    }
  });
});
