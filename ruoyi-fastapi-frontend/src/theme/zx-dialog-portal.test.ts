import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import useSettingsStore from '@/store/modules/settings';
import {
  projectZxThemeScope,
  setZxThemePreference,
  zxThemeConfig,
  zxThemePreference,
} from './zx-theme-config';

beforeEach(() => {
  setActivePinia(createPinia());
  setZxThemePreference({
    themeId: 'default',
    mode: 'light',
    density: 'default',
  });
  document.documentElement.removeAttribute('data-zx-theme');
  document.documentElement.removeAttribute('data-zx-variant');
  document.documentElement.classList.remove('dark');
});

describe('theme preference ownership', () => {
  it('shares the same preference between selector, Settings and Provider without reading DOM', () => {
    const settings = useSettingsStore();
    document.documentElement.classList.add('dark');
    expect(settings.isDark).toBe(false);
    settings.toggleTheme();
    setZxThemePreference({ themeId: 'factory-blue', density: 'compact' });
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
});
