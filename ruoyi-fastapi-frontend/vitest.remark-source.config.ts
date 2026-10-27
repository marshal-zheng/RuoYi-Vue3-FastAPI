import { createRequire } from 'node:module';
import path from 'node:path';
import vueJsx from '@vitejs/plugin-vue-jsx';
import { mergeConfig } from 'vitest/config';
import base from './vitest.config';

const workspaceRoot = process.env.VITE_ZXIO_REPO_ROOT;
if (!workspaceRoot) throw new Error('Set VITE_ZXIO_REPO_ROOT to the prepared ZXUI checkout');
const hostRequire = createRequire(path.resolve(workspaceRoot, 'package.json'));
const packageRequire = createRequire(
  path.resolve(workspaceRoot, 'packages/theme-compiler/package.json')
);
const { require: requireSource } = hostRequire('tsx/cjs/api');
const { zxuiSourcePlugin } = requireSource(
  packageRequire.resolve('@zxio/theme-compiler/vite/source'),
  packageRequire.resolve('@zxio/theme-compiler/package.json')
);

const config = mergeConfig(base, {
  plugins: [
    // Source-mode editor chrome includes Vue TSX, as in the dev server config.
    vueJsx(),
    zxuiSourcePlugin({
      workspaceRoot,
      featurePackages: ['@zxio/text-editor', '@zxio/schema-form'],
    }),
  ],
  resolve: {
    dedupe: [
      'vue',
      'element-plus',
      '@formily/core',
      '@formily/vue',
      '@formily/reactive',
      '@formily/shared',
    ],
  },
});
// mergeConfig concatenates array values; replace include after the merge.
config.test!.include = [
  'tests/unit/components/RemarkPackageRoundtrip.test.ts',
  'tests/unit/components/RemarkFormilyIntegration.test.ts',
  'tests/unit/components/RemarkAIIntegration.test.ts',
  'src/ai-context/status.test.ts',
  'src/api/system/textFieldAi.test.ts',
  'tests/unit/ai-context-contract.test.ts',
  'tests/unit/ai-context-manifest.test.ts',
];
export default config;
