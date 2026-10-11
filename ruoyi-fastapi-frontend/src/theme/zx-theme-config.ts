import { computed, readonly, ref } from 'vue';
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

const preference = ref<ZxThemePreference>(readPreference());
export const zxThemePreference = readonly(preference);
export const zxThemeId = computed(() => preference.value.themeId);
export const zxIsDark = computed(() =>
  preference.value.mode === 'system' ? preferredDark.value : preference.value.mode === 'dark'
);

/** The only preference write path; Provider resolves concrete variants and commits CSS. */
export function setZxThemePreference(update: Partial<ZxThemePreference>): void {
  const next = { ...preference.value, ...update };
  if (
    !isZxThemeId(next.themeId) ||
    !validModes.has(next.mode) ||
    !validDensities.has(next.density)
  ) {
    throw new Error(`Invalid ZXUI theme preference: ${JSON.stringify(update)}`);
  }
  if (
    Object.keys(update).every(
      (key) =>
        next[key as keyof ZxThemePreference] === preference.value[key as keyof ZxThemePreference]
    )
  )
    return;
  preference.value = next;
  try {
    localStorage.setItem(PREFERENCE_STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* A readable active theme does not require storage. */
  }
}

/** DOM attributes are a projection of the Host's committed scope, never an input. */
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
