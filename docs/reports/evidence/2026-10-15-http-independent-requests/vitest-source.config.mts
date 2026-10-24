import { mergeConfig } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/node_modules/vite/dist/node/index.js'
import base from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vitest.config.ts'
export default mergeConfig(base, {
  root: '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend',
  resolve: {
    alias: [{find: /^@zxio\/http$/, replacement: '/Users/hqz/Downloads/element-plus/packages/http/src/index.ts'}],
    dedupe: ['axios'],
  },
  test: { reporters: ['default'] },
})

