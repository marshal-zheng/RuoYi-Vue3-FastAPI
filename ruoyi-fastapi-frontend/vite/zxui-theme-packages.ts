import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { ZX_THEME_PACKAGE_CHOICES } from '../src/theme/zx-theme-packages';

/** UI, Host registrations and build inputs all originate in this catalog. */
export const ZXUI_THEME_PACKAGE_NAMES = ZX_THEME_PACKAGE_CHOICES.map(
  (choice) => choice.packageName
);

function loadThemeCompiler(frontendRoot: string, workspaceRoot?: string) {
  const compilerRequire = createRequire(
    path.resolve(workspaceRoot || frontendRoot, 'package.json')
  );
  if (!workspaceRoot) {
    return compilerRequire(
      '@zxio/theme-compiler/vite'
    ) as typeof import('@zxio/theme-compiler/vite');
  }
  // The public source facet keeps Vite tooling and browser components on the same revision.
  // tsx belongs to the prepared ZXUI checkout; nothing is globally registered.
  const { require: requireSource } = compilerRequire('tsx/cjs/api');
  return requireSource(
    '@zxio/theme-compiler/vite/source',
    compilerRequire.resolve('@zxio/theme-compiler/package.json')
  ) as typeof import('@zxio/theme-compiler/vite');
}

export function zxuiThemeDeploymentPlugin(options: {
  frontendRoot: string;
  localRepoRoot?: string;
}) {
  const { frontendRoot, localRepoRoot } = options;
  const declared = JSON.parse(fs.readFileSync(path.resolve(frontendRoot, 'package.json'), 'utf8'));
  for (const packageName of ZXUI_THEME_PACKAGE_NAMES) {
    if (!declared.dependencies?.[packageName]) {
      throw new Error(
        `[zxui-theme] Registered theme is not declared in dependencies: ${packageName}`
      );
    }
  }
  const { themeDeploymentPlugin } = loadThemeCompiler(frontendRoot, localRepoRoot);
  return themeDeploymentPlugin({
    packages: ZX_THEME_PACKAGE_CHOICES.map(({ packageName, id }) => ({
      packageName,
      themeId: id,
    })),
    resolveFrom: path.resolve(frontendRoot, 'package.json'),
    workspaceRoot: localRepoRoot,
  });
}

/** Select the library-owned source plugin from the same checkout as its components. */
export function zxuiSourceIntegrationPlugin(frontendRoot: string, workspaceRoot: string) {
  const { zxuiSourcePlugin } = loadThemeCompiler(frontendRoot, workspaceRoot);
  return zxuiSourcePlugin({
    workspaceRoot,
    featurePackages: [
      '@zxio/chart',
      '@zxio/dashboard',
      '@zxio/http',
      '@zxio/theme-tailwind',
      '@zxio/vue-query',
    ],
  });
}
