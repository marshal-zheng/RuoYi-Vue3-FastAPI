import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import jsx from '@vitejs/plugin-vue-jsx';
import createSvgIcon from '../../../vite/plugins/svg-icon';
import AutoImport from 'unplugin-auto-import/vite';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  zxuiSourceIntegrationPlugin,
  zxuiThemeDeploymentPlugin,
} from '../../../vite/zxui-theme-packages';
const root = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(root, '../../..');
const library = process.env.VITE_ZXIO_REPO_ROOT;
if (!library) throw new Error('Set VITE_ZXIO_REPO_ROOT to the optimization worktree');
export default defineConfig({
  root,
  cacheDir: resolve(frontend, 'node_modules/.vite/table-render-pilots'),
  plugins: [
    vue(),
    jsx(),
    createSvgIcon(true),
    AutoImport({ imports: ['vue', 'vue-router', 'pinia'], dts: false }),
    zxuiSourceIntegrationPlugin(frontend, library),
    zxuiThemeDeploymentPlugin({
      frontendRoot: frontend,
      localRepoRoot: library,
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(frontend, 'src'),
      '@table-render-benchmark.vue': resolve(
        library,
        'docs/examples/table-render/performance-workbench.vue'
      ),
    },
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue'],
    dedupe: [
      'vue',
      'element-plus',
      '@vue/runtime-core',
      '@vue/runtime-dom',
      '@vue/reactivity',
      '@vue/shared',
    ],
  },
  define: { 'import.meta.env.VITE_APP_RUNTIME_MODE': JSON.stringify('real') },
  server: {
    host: '127.0.0.1',
    port: 5198,
    strictPort: true,
    open: false,
    fs: { allow: [frontend, library] },
  },
  preview: { host: '127.0.0.1', port: 5198, strictPort: true, open: false },
  build: {
    target: 'esnext',
    outDir: resolve(frontend, 'node_modules/.cache/table-render-pilots'),
    emptyOutDir: true,
  },
});
