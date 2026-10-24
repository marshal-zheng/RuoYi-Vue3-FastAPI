import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import jsx from '@vitejs/plugin-vue-jsx';
import tailwindcss from '@tailwindcss/vite';
import AutoImport from 'unplugin-auto-import/vite';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { zxuiSourceIntegrationPlugin } from '../../../vite/zxui-theme-packages';

const root = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(root, '../../..');
const library =
  process.env.ZXUI_LAYOUT_REPO || '/Users/hqz/Downloads/element-plus';
const realSettings = process.env.LAYOUT_TEST_REAL_SETTINGS === '1';
export default defineConfig({
  root,
  cacheDir: resolve(
    frontend,
    `node_modules/.vite/layout-regions-${process.env.LAYOUT_TEST_INSTALLED === '1' ? 'installed' : 'source'}${realSettings ? '-preferences' : ''}`,
  ),
  plugins: [
    vue(),
    jsx(),
    tailwindcss(),
    AutoImport({ imports: ['vue', 'vue-router', 'pinia'], dts: false }),
    ...(process.env.LAYOUT_TEST_INSTALLED === '1'
      ? []
      : [zxuiSourceIntegrationPlugin(frontend, library)]),
  ],
  resolve: {
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue'],
    alias: [
      { find: /^@\/router$/, replacement: resolve(root, 'router.ts') },
      {
        find: '@/store/modules/settings',
        replacement: realSettings
          ? resolve(frontend, 'src/store/modules/settings.ts')
          : resolve(root, 'settings.ts'),
      },
      ...(realSettings
        ? [
            {
              find: '@/theme/zx-theme-config',
              replacement: resolve(root, 'theme-preference.ts'),
            },
          ]
        : []),
      { find: '@/store/modules/user', replacement: resolve(root, 'user.ts') },
      {
        find: '@/store/modules/permission',
        replacement: resolve(root, 'permission.ts'),
      },
      {
        find: '@/theme/ZxThemePresetSwitch.vue',
        replacement: resolve(root, 'ThemeSwitch.vue'),
      },
      { find: '@', replacement: resolve(frontend, 'src') },
    ],
    dedupe: [
      'vue',
      'element-plus',
      '@vue/runtime-core',
      '@vue/runtime-dom',
      '@vue/reactivity',
      '@vue/shared',
    ],
  },
  optimizeDeps: { entries: ['index.html'] },
  server: {
    host: '127.0.0.1',
    port: Number(process.env.LAYOUT_TEST_PORT || 4196),
    strictPort: true,
    fs: { allow: [frontend, library] },
  },
  build: {
    target: 'esnext',
    outDir: resolve(frontend, 'node_modules/.cache/layout-regions'),
    emptyOutDir: true,
  },
});
