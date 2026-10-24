import { describe, expect, it } from 'vitest';

import { ZX_THEME_PACKAGE_CHOICES, isZxThemeId } from './zx-theme-packages';

describe('ZX_THEME_PACKAGE_CHOICES', () => {
  it('lists the currently enabled ZXUI presets', () => {
    expect(ZX_THEME_PACKAGE_CHOICES).toHaveLength(9);
    expect(ZX_THEME_PACKAGE_CHOICES.map((choice) => choice.id)).toEqual([
      'default',
      'defense-green',
      'army-pine',
      'air-gray',
      'pap-olive',
      'rocket-moss',
      'factory-blue',
      'tech-blue',
      'industrial-blue',
    ]);
    expect(isZxThemeId('factory-blue')).toBe(true);
    expect(isZxThemeId('rocket-moss')).toBe(true);
    expect(isZxThemeId('not-a-theme')).toBe(false);
  });
});
