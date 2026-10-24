import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import useSettingsStore from '@/store/modules/settings';
import {
  setZxThemePreference,
  zxThemePreference,
  zxThemePreferences,
} from '@/theme/zx-theme-config';

vi.mock('@/utils/dynamicTitle', () => ({ useDynamicTitle: vi.fn() }));
vi.mock('@vueuse/core', () => ({ usePreferredDark: vi.fn(() => ({ value: false })) }));

let releasePreference: (() => void) | undefined;
afterEach(() => releasePreference?.());

describe('layout settings and ZXUI theme ownership', () => {
  beforeEach(async () => {
    localStorage.clear();
    setActivePinia(createPinia());
    releasePreference = zxThemePreferences.bind(async () => true);
    await setZxThemePreference({ themeId: 'default', mode: 'light', density: 'default' });
  });

  it('restores layout options without restoring retired colour settings', () => {
    localStorage.setItem(
      'layout-setting',
      JSON.stringify({ topNav: true, sideTheme: 'theme-dark', theme: '#ff0000' })
    );

    const store = useSettingsStore();
    expect(store.topNav).toBe(true);
    expect('sideTheme' in store.$state).toBe(false);
    expect('theme' in store.$state).toBe(false);
    expect(zxThemePreference.value.themeId).toBe('default');
  });

  it('rejects retired colour settings while retaining layout changes', () => {
    const store = useSettingsStore();
    store.changeSetting({ key: 'sideTheme', value: 'theme-dark' });
    store.changeSetting({ key: 'theme', value: '#ff0000' });
    store.changeSetting({ key: 'tagsView', value: false });

    expect('sideTheme' in store.$state).toBe(false);
    expect('theme' in store.$state).toBe(false);
    expect(store.tagsView).toBe(false);
  });

  it('awaits committed mode changes through ZXUI preference', async () => {
    const store = useSettingsStore();
    const pending = store.toggleTheme();
    expect(pending).toBeInstanceOf(Promise);
    await pending;
    expect(zxThemePreference.value.mode).toBe('dark');
    expect(store.isDark).toBe(true);
    await store.toggleTheme();
    expect(zxThemePreference.value.mode).toBe('light');
  });
});
