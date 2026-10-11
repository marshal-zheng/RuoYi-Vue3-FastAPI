import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import type { Plugin } from 'vite';

import { ZX_THEME_PACKAGE_CHOICES } from '../src/theme/zx-theme-packages';

/** UI, Host registrations and build inputs all originate in this catalog. */
export const ZXUI_THEME_PACKAGE_NAMES = ZX_THEME_PACKAGE_CHOICES.map(
  (choice) => choice.packageName
);

const VIRTUAL_ID = 'virtual:zxui-theme-deployment';
const ASSET_DIRECTORY = 'zx-theme-assets';

/** Local source resolution belongs only to the build tool, never the browser. */
function localResolutionAnchor(frontendRoot: string, repoRoot: string): string {
  const anchorRoot = path.resolve(frontendRoot, 'node_modules/.cache/zxui-theme-source');
  const scopeRoot = path.resolve(anchorRoot, 'node_modules/@zxio');
  fs.mkdirSync(scopeRoot, { recursive: true });
  for (const packageName of ZXUI_THEME_PACKAGE_NAMES) {
    const source = path.resolve(repoRoot, 'packages', packageName.slice('@zxio/'.length));
    const metadataPath = path.join(source, 'package.json');
    if (!fs.existsSync(metadataPath)) {
      throw new Error(`[zxui-theme] Missing registered package: ${packageName} (${metadataPath})`);
    }
    const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    if (metadata.name !== packageName) {
      throw new Error(`[zxui-theme] Package identity mismatch: ${packageName}`);
    }
    const target = path.resolve(scopeRoot, packageName.slice('@zxio/'.length));
    if (fs.existsSync(target) && fs.realpathSync(target) === fs.realpathSync(source)) continue;
    try {
      if (!fs.lstatSync(target).isSymbolicLink()) {
        throw new Error(`[zxui-theme] Refusing to overwrite unmanaged package: ${target}`);
      }
      fs.unlinkSync(target);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
    fs.symlinkSync(source, target, 'dir');
  }
  return path.join(anchorRoot, 'package.json');
}

export function resolveZxuiThemeAssetRequest(
  url: string,
  base: string,
  outputDir: string
): string | null {
  let pathname: string;
  try {
    pathname = decodeURIComponent(new URL(url, 'http://vite.local').pathname);
  } catch {
    return null;
  }
  const basePath =
    base === './' || base === '/'
      ? ''
      : new URL(base, 'http://vite.local').pathname.replace(/\/$/, '');
  const prefix = `${basePath}/${ASSET_DIRECTORY}/`;
  if (!pathname.startsWith(prefix)) return null;
  const file = path.resolve(outputDir, pathname.slice(prefix.length));
  const relative = path.relative(outputDir, file);
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) return null;
  if (!['.css', '.json'].includes(path.extname(file))) return null;
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return null;
  return file;
}

/** Public manifest/CSS exports are emitted together, with their original hashes. */
export function zxuiThemeDeploymentPlugin(options: {
  frontendRoot: string;
  localRepoRoot?: string;
  serve?: boolean;
}): Plugin {
  const { frontendRoot, localRepoRoot } = options;
  // A build may run while Vite is serving a different source/candidate package.
  // Keep its owned asset directory separate so neither emitter invalidates the other's map.
  const outputDir = path.resolve(
    frontendRoot,
    options.serve ? 'node_modules/.cache/zxui-theme-deployment' : `public/${ASSET_DIRECTORY}`
  );
  const compilerRequire = createRequire(
    path.resolve(localRepoRoot || frontendRoot, 'package.json')
  );
  const { emitThemeDeployment } = compilerRequire('@zxio/theme-compiler/deployment') as Pick<
    typeof import('@zxio/theme-compiler/deployment'),
    'emitThemeDeployment'
  >;
  const resolveFrom = localRepoRoot
    ? localResolutionAnchor(frontendRoot, localRepoRoot)
    : path.resolve(frontendRoot, 'package.json');
  const declared = JSON.parse(fs.readFileSync(path.resolve(frontendRoot, 'package.json'), 'utf8'));
  const packageRequire = createRequire(resolveFrom);
  for (const packageName of ZXUI_THEME_PACKAGE_NAMES) {
    if (!declared.dependencies?.[packageName]) {
      throw new Error(
        `[zxui-theme] Registered theme is not declared in dependencies: ${packageName}`
      );
    }
    try {
      const manifestPath = packageRequire.resolve(`${packageName}/manifest.json`);
      JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    } catch (error) {
      throw new Error(
        `[zxui-theme] Registered manifest unavailable: ${packageName}/manifest.json`,
        { cause: error }
      );
    }
  }
  const emitted = emitThemeDeployment({
    packages: ZXUI_THEME_PACKAGE_NAMES,
    resolveFrom,
    outputDir,
    assetBasePath: ASSET_DIRECTORY,
  });
  if (!emitted.ok) {
    throw new Error(`[zxui-theme] Deployment failed: ${JSON.stringify(emitted.diagnostics)}`);
  }
  for (const choice of ZX_THEME_PACKAGE_CHOICES) {
    if (
      !emitted.value.registrations.some(
        ({ manifest }) =>
          manifest.identity.themeId === choice.id &&
          manifest.identity.packageName === choice.packageName
      )
    ) {
      throw new Error(
        `[zxui-theme] Registered manifest identity mismatch: ${choice.packageName}/${choice.id}`
      );
    }
  }
  return {
    name: 'zxui-theme-deployment',
    resolveId(id) {
      if (id === VIRTUAL_ID) return `\0${VIRTUAL_ID}`;
      return null;
    },
    load(id) {
      if (id !== `\0${VIRTUAL_ID}`) return;
      // JSON.parse retains exact manifest data while avoiding a huge JS object AST.
      return `export default JSON.parse(${JSON.stringify(JSON.stringify(emitted.value))});`;
    },
    configureServer(server) {
      // Vite CSS transforms would change hashed bytes. Serve deployment files verbatim.
      server.middlewares.use((req, res, next) => {
        if (req.method !== 'GET' && req.method !== 'HEAD') return next();
        const file = resolveZxuiThemeAssetRequest(req.url || '', server.config.base, outputDir);
        if (!file) return next();
        const bytes = fs.readFileSync(file);
        res.setHeader(
          'Content-Type',
          path.extname(file) === '.css' ? 'text/css' : 'application/json'
        );
        res.setHeader('Content-Length', bytes.byteLength);
        res.setHeader('Cache-Control', 'no-cache');
        res.end(req.method === 'HEAD' ? undefined : bytes);
      });
    },
  };
}

/** Select the library-owned source plugin from the same checkout as its components. */
export function zxuiSourceIntegrationPlugin(frontendRoot: string, workspaceRoot: string) {
  const compilerRequire = createRequire(
    path.resolve(workspaceRoot || frontendRoot, 'package.json')
  );
  const { zxuiSourcePlugin } = compilerRequire(
    '@zxio/theme-compiler/vite'
  ) as typeof import('@zxio/theme-compiler/vite');
  return zxuiSourcePlugin({ workspaceRoot, featurePackages: ['@zxio/chart'] });
}
