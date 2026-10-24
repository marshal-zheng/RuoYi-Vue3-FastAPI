import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import useSettingsStore from '@/store/modules/settings';

vi.mock('@/utils/dynamicTitle', () => ({ useDynamicTitle: vi.fn() }));
vi.mock('@/theme/zx-theme-config', () => ({
  setZxThemePreference: vi.fn(),
  zxIsDark: { value: false },
}));

describe('independent chrome preferences', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it('defaults to a visible header and breadcrumb with tags disabled', () => {
    const store = useSettingsStore();
    expect(store.headerVisible).toBe(true);
    expect(store.breadcrumbVisible).toBe(true);
    expect(store.tagsView).toBe(false);
  });

  it('restores independent saved visibility choices', () => {
    localStorage.setItem(
      'layout-setting',
      JSON.stringify({
        layoutVersion: 1,
        headerVisible: false,
        breadcrumbVisible: false,
        tagsView: true,
      })
    );
    const store = useSettingsStore();
    expect(store.headerVisible).toBe(false);
    expect(store.breadcrumbVisible).toBe(false);
    expect(store.tagsView).toBe(true);
  });

  it('migrates enabled tags once, retains supported chrome preferences and drops retired keys', () => {
    localStorage.setItem(
      'layout-setting',
      JSON.stringify({
        tagsView: true,
        headerVisible: false,
        breadcrumbVisible: false,
        sidebarLogo: false,
        fixedHeader: true,
      })
    );
    const store = useSettingsStore();
    expect(store.tagsView).toBe(false);
    expect(store.headerVisible).toBe(false);
    expect(store.breadcrumbVisible).toBe(false);
    expect(store.sidebarLogo).toBe(false);
    const saved = JSON.parse(localStorage.getItem('layout-setting')!);
    expect(saved).toEqual({
      layoutVersion: 1,
      tagsView: false,
      headerVisible: false,
      breadcrumbVisible: false,
      sidebarLogo: false,
    });

    expect(saved).not.toHaveProperty('fixedHeader');

    // A deliberate choice made after migration must survive the next startup.
    localStorage.setItem('layout-setting', JSON.stringify({ ...saved, tagsView: true }));
    setActivePinia(createPinia());
    expect(useSettingsStore().tagsView).toBe(true);
  });

  it('uses defaults for malformed persisted tags and null settings', () => {
    localStorage.setItem('layout-setting', JSON.stringify({ layoutVersion: 1, tagsView: 'false' }));
    expect(useSettingsStore().tagsView).toBe(false);
    setActivePinia(createPinia());
    localStorage.setItem('layout-setting', 'null');
    expect(useSettingsStore().tagsView).toBe(false);
  });
});
