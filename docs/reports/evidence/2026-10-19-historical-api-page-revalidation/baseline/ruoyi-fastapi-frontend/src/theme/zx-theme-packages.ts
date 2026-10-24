export interface ZxThemePackageChoice {
  readonly id: string;
  readonly packageName: `@zxio/theme-${string}`;
  readonly label: string;
  readonly swatch: string;
}

/**
 * Single application catalog: selector, Host and build deployment derive from it.
 * A missing declared package or manifest is a deployment error.
 */
export const ZX_THEME_PACKAGE_CHOICES: readonly ZxThemePackageChoice[] = [
  {
    id: 'default',
    packageName: '@zxio/theme-default',
    label: '默认',
    swatch: 'linear-gradient(135deg, #2f6bff 0%, #5f86ff 100%)',
  },
  {
    id: 'defense-green',
    packageName: '@zxio/theme-defense-green',
    label: '苔绿',
    swatch: 'linear-gradient(135deg, #35452d 0%, #5d7250 52%, #889b79 100%)',
  },
  {
    id: 'army-pine',
    packageName: '@zxio/theme-army-pine',
    label: '森绿',
    swatch: 'linear-gradient(135deg, #1a211f 0%, #476656 52%, #7f9e8a 100%)',
  },
  {
    id: 'air-gray',
    packageName: '@zxio/theme-air-gray',
    label: '雾蓝',
    swatch: 'linear-gradient(135deg, #171e2b 0%, #38546b 55%, #7a9bb3 100%)',
  },
  {
    id: 'pap-olive',
    packageName: '@zxio/theme-pap-olive',
    label: '琥珀',
    swatch: 'linear-gradient(135deg, #1c2117 0%, #455233 52%, #c28f29 100%)',
  },
  {
    id: 'rocket-moss',
    packageName: '@zxio/theme-rocket-moss',
    label: '墨青',
    swatch: 'linear-gradient(135deg, #141e19 0%, #2e4c38 52%, #c79e47 100%)',
  },
  {
    id: 'factory-blue',
    packageName: '@zxio/theme-factory-blue',
    label: '钢蓝',
    swatch: 'linear-gradient(135deg, #16202e 0%, #3b78b3 55%, #8fb8e8 100%)',
  },
  {
    id: 'tech-blue',
    packageName: '@zxio/theme-tech-blue',
    label: '科技蓝',
    swatch: 'linear-gradient(135deg, #0f62fe 0%, #4589ff 55%, #a6c8ff 100%)',
  },
  {
    id: 'industrial-blue',
    packageName: '@zxio/theme-industrial-blue',
    label: '工厂蓝',
    swatch: 'linear-gradient(135deg, #0e4ab8 0%, #2db3ff 58%, #98dcff 100%)',
  },
];

export const ZX_DEFAULT_THEME_ID = 'default';
export const ZX_THEME_STORAGE_KEY = 'zx-theme-preset';
export const ZX_THEME_MANIFEST_LIMIT = ZX_THEME_PACKAGE_CHOICES.length;

export function isZxThemeId(value: string): boolean {
  return ZX_THEME_PACKAGE_CHOICES.some((choice) => choice.id === value);
}
