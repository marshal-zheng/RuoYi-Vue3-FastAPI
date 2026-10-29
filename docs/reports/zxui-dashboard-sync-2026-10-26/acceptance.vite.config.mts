import { defineConfig, mergeConfig } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/node_modules/vite/dist/node/index.js';
import { writeFileSync } from 'node:fs';
import base from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vite.config';
const report = '/Users/hqz/dev/RuoYi-Vue3-FastAPI/docs/reports/zxui-dashboard-sync-2026-10-26';
export default defineConfig(async (env) => {
  const source = process.env.VITE_ZXUI_LOCAL === 'true';
  const label = source ? 'source' : 'packed';
  return mergeConfig(await (base as Function)(env), {
    cacheDir: `/Users/hqz/dev/RuoYi-Vue3-FastAPI/.tmp/zxui-dashboard-sync/cache-${label}`,
    server: { open: false },
    plugins: [{ name: 'qa-module-provenance',
      configResolved(config) {
        writeFileSync(`${report}/${label}-config.json`, JSON.stringify({ mode: config.mode, command: config.command, plugins: config.plugins.map(p => p.name), dedupe: config.resolve.dedupe, cacheDir: config.cacheDir }, null, 2));
      },
      configureServer(server) {
        server.middlewares.use('/__qa/modules', (_req, res) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify([...server.moduleGraph.idToModuleMap.keys()])); });
      },
      generateBundle() { writeFileSync(`${report}/${label}-build-modules.json`, JSON.stringify([...this.getModuleIds()], null, 2)); },
    }],
  });
});
