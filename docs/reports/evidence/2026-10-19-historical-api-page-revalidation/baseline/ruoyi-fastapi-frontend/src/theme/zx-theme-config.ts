import { computed } from 'vue';
import { createThemePreferenceController } from '@zxio/zxui/theme-host';
import { usePreferredDark } from '@vueuse/core';

import {
  ZX_DEFAULT_THEME_ID,
  ZX_THEME_PACKAGE_CHOICES,
  ZX_THEME_STORAGE_KEY,
  isZxThemeId,
} from './zx-theme-packages';

export type ZxThemeMode = 'light' | 'dark' | 'system';
export type ZxThemeDensity = 'compact' | 'default' | 'comfortable';
export interface ZxThemePreference {
  readonly themeId: string;
  readonly mode: ZxThemeMode;
  readonly density: ZxThemeDensity;
}

const PREFERENCE_STORAGE_KEY = 'zx-theme-preference';
const validModes = new Set<ZxThemeMode>(['light', 'dark', 'system']);
const validDensities = new Set<ZxThemeDensity>(['compact', 'default', 'comfortable']);
const preferredDark = usePreferredDark();

function readPreference(): ZxThemePreference {
  const fallback: ZxThemePreference = {
    themeId: ZX_DEFAULT_THEME_ID,
    mode: 'system',
    density: 'default',
  };
  try {
    const saved = JSON.parse(localStorage.getItem(PREFERENCE_STORAGE_KEY) || 'null');
    // Read existing preferences once; only the new preference object is written afterwards.
    const themeId = saved?.themeId ?? localStorage.getItem(ZX_THEME_STORAGE_KEY);
    const legacyMode = localStorage.getItem('vueuse-color-scheme');
    const mode = saved?.mode ?? (legacyMode === 'auto' ? 'system' : legacyMode);
    return {
      themeId: typeof themeId === 'string' && isZxThemeId(themeId) ? themeId : fallback.themeId,
      mode: validModes.has(mode) ? mode : fallback.mode,
      density: validDensities.has(saved?.density) ? saved.density : fallback.density,
    };
  } catch {
    return fallback;
  }
}

// The business owns its catalog, storage key and legacy migration; ZXUI owns switching.
export const zxThemePreferences = createThemePreferenceController<ZxThemePreference>({
  initial: readPreference(),
  validate(next) {
    if (
      !isZxThemeId(next.themeId) ||
      !validModes.has(next.mode) ||
      !validDensities.has(next.density)
    ) {
      throw new Error(`Invalid ZXUI theme preference: ${JSON.stringify(next)}`);
    }
  },
  persist(next) {
    localStorage.setItem(PREFERENCE_STORAGE_KEY, JSON.stringify(next));
  },
});
const preference = zxThemePreferences.preference;
export const zxThemePreference = preference;
export const zxThemePreferencePending = zxThemePreferences.pending;
export const zxThemeId = computed(() => preference.value.themeId);
export const zxIsDark = computed(() =>
  preference.value.mode === 'system' ? preferredDark.value : preference.value.mode === 'dark'
);
export const setZxThemePreference = zxThemePreferences.set;
/** Compatibility port for existing consumers; production binds directly to the Host. */
export const bindZxThemePreferenceUpdater = zxThemePreferences.bind;

/** @deprecated Production uses the Host-owned body portal scope; retained for legacy callers. */
export function projectZxThemeScope(resolved: {
  readonly themeId: string;
  readonly variantKey: string;
  readonly selection: { readonly mode: string };
}): void {
  document.documentElement.dataset.zxTheme = resolved.themeId;
  document.documentElement.dataset.zxVariant = resolved.variantKey;
}

export const zxThemeConfig = computed(() => ({
  ...preference.value,
  portalTarget: () => document.body,
}));

export function zxThemeChoice(themeId: string = zxThemeId.value) {
  return (
    ZX_THEME_PACKAGE_CHOICES.find((choice) => choice.id === themeId) ?? ZX_THEME_PACKAGE_CHOICES[0]
  );
}
