import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import jsx from '@vitejs/plugin-vue-jsx';
import AutoImport from 'unplugin-auto-import/vite';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readFileSync, existsSync } from 'node:fs';
const fixtureRoot = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(fixtureRoot, '../../..');
export default defineConfig({
  root: fixtureRoot,
  cacheDir: resolve(frontendRoot, 'node_modules/.vite/ui-convergence'),
  plugins: [
    vue(),
    jsx(),
    AutoImport({ imports: ['vue', 'vue-router', 'pinia'], dts: false }),
    {
      name: 'fixture-exact-theme-css',
      configureServer(server) {
        server.middlewares.use((request, response, next) => {
          const pathname = request.url?.split('?')[0] ?? '';
          if (!/^\/zx-theme-assets\/[a-f0-9]+\.css$/.test(pathname)) return next();
          const file = resolve(fixtureRoot, `public${pathname}`);
          if (!existsSync(file)) return next();
          response.setHeader('Content-Type', 'text/css');
          response.end(readFileSync(file));
        });
      },
    },
  ],
  resolve: {
    alias: { '@': resolve(frontendRoot, 'src') },
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
    port: 4182,
    strictPort: true,
    fs: { allow: [frontendRoot] },
  },
});
