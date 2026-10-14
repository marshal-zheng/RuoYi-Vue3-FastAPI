import { describe, expect, it } from 'vitest';
import { ZXUI_THEME_PACKAGE_NAMES } from '../../vite/zxui-theme-packages';
import { ZX_THEME_PACKAGE_CHOICES } from './zx-theme-packages';

describe('theme deployment registration', () => {
  it('derives build packages from the selector catalog', () => {
    expect(ZXUI_THEME_PACKAGE_NAMES).toEqual(
      ZX_THEME_PACKAGE_CHOICES.map(({ packageName }) => packageName)
    );
  });
});
