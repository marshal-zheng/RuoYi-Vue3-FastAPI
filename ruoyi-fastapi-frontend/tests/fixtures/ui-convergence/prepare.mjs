import { build } from 'esbuild';
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const fixtureRoot = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(fixtureRoot, '../../..');
const bundle = resolve(fixtureRoot, '.generator.mjs');
await build({
  absWorkingDir: frontendRoot,
  entryPoints: [resolve(fixtureRoot, 'generate.ts')],
  outfile: bundle,
  bundle: true,
  platform: 'node',
  format: 'esm',
  packages: 'external',
  loader: { '.jpg': 'dataurl' },
  define: { 'import.meta.env': '{}' },
  alias: { '@': resolve(frontendRoot, 'src') },
  plugins: [
    {
      name: 'pure-generator-imports',
      setup(builder) {
        // Generator utilities are pure exports. Do not execute unrelated browser bootstrap
        // side effects re-exported by src/utils/index.ts when producing an SFC in Node.
        builder.onResolve({ filter: /.*/ }, async (args) => {
          if (args.pluginData) return;
          const result = await builder.resolve(args.path, {
            kind: args.kind,
            resolveDir: args.resolveDir,
            pluginData: true,
          });
          return { ...result, sideEffects: false };
        });
      },
    },
  ],
});
execFileSync(process.execPath, [bundle], { cwd: frontendRoot, stdio: 'inherit' });
