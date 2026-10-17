import { resolve } from 'node:path';
import { defineConfig } from 'vitest/config';
import { zxuiSourceIntegrationPlugin } from '../../../vite/zxui-theme-packages';

const frontendRoot = resolve(__dirname, '../../..');
const source = process.env.VITE_ZXUI_LOCAL === 'true';

export default defineConfig({
  root: frontendRoot,
  plugins: source
    ? [
        zxuiSourceIntegrationPlugin(
          frontendRoot,
          process.env.VITE_ZXIO_REPO_ROOT || '/Users/hqz/Downloads/element-plus'
        ),
      ]
    : [],
  resolve: { alias: { '@': resolve(frontendRoot, 'src') } },
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost/' } },
    // Deliberately exclude repository setup/MSW. Every API request uses real local HTTP.
    setupFiles: [],
    include: ['tests/manual/role-authorization/real-api.probe.ts'],
    server: { deps: { inline: ['element-plus'] } },
    testTimeout: 90_000,
    reporters: ['dot'],
    env: {
      VITE_APP_BASE_API: process.env.CODEX_ROLE_API_BASE || 'http://127.0.0.1:8088',
      VITE_APP_RUNTIME_MODE: 'real',
      VITE_ENABLE_MOCK: 'off',
    },
  },
});
