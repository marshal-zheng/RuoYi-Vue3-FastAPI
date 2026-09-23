import { afterAll, describe, expect, it } from 'vitest';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import {
  resolveZxuiThemeAssetRequest,
  ZXUI_THEME_PACKAGE_NAMES,
} from '../../vite/zxui-theme-packages';
import { ZX_THEME_PACKAGE_CHOICES } from './zx-theme-packages';

const output = mkdtempSync(path.join(tmpdir(), 'zx-theme-assets-test-'));
mkdirSync(path.join(output, 'css'));
writeFileSync(path.join(output, 'css/test.css'), ':root { color: red; }');
afterAll(() => rmSync(output, { recursive: true, force: true }));

describe('theme deployment boundary', () => {
  it('derives build packages from the selector catalog', () => {
    expect(ZXUI_THEME_PACKAGE_NAMES).toEqual(
      ZX_THEME_PACKAGE_CHOICES.map(({ packageName }) => packageName)
    );
  });

  it.each(['/', '/admin/', './'])('serves original CSS below the %s application base', (base) => {
    const prefix = base === '/admin/' ? '/admin/' : '/';
    expect(
      resolveZxuiThemeAssetRequest(`${prefix}zx-theme-assets/css/test.css?x=1`, base, output)
    ).toBe(path.join(output, 'css/test.css'));
  });

  it.each(['/zx-theme-assets/%2e%2e%2foutside.css', '/zx-theme-assets/%ZZ', '/other/css/test.css'])(
    'rejects requests outside the deployment: %s',
    (url) => {
      expect(resolveZxuiThemeAssetRequest(url, '/', output)).toBeNull();
    }
  );
});
