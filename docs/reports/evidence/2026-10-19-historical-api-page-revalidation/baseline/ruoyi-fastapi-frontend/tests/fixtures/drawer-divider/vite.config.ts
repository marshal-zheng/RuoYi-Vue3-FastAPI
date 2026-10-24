import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import jsx from '@vitejs/plugin-vue-jsx';
import AutoImport from 'unplugin-auto-import/vite';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  zxuiSourceIntegrationPlugin,
  zxuiThemeDeploymentPlugin,
} from '../../../vite/zxui-theme-packages';

const root = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(root, '../../..');
const library = process.env.ZXUI_LAYOUT_REPO || '/Users/hqz/Downloads/element-plus';
const installed = process.env.DRAWER_TEST_INSTALLED === '1';
export default defineConfig({
  root,
  cacheDir: resolve(
    frontend,
    `node_modules/.vite/drawer-divider-${installed ? 'installed' : 'source'}`
  ),
  plugins: [
    vue(),
    jsx(),
    AutoImport({ imports: ['vue', 'vue-router', 'pinia'], dts: false }),
    ...(installed ? [] : [zxuiSourceIntegrationPlugin(frontend, library)]),
    zxuiThemeDeploymentPlugin({
      frontendRoot: frontend,
      localRepoRoot: library,
    }),
  ],
  resolve: {
    alias: { '@': resolve(frontend, 'src') },
    dedupe: [
      'vue',
      'element-plus',
      '@vue/runtime-core',
      '@vue/runtime-dom',
      '@vue/reactivity',
      '@vue/shared',
    ],
  },
  server: {
    host: '127.0.0.1',
    port: Number(process.env.DRAWER_TEST_PORT || 4199),
    strictPort: true,
    fs: { allow: [frontend, library] },
  },
  build: {
    target: 'esnext',
    outDir: resolve(frontend, 'node_modules/.cache/drawer-divider'),
    emptyOutDir: true,
  },
});
