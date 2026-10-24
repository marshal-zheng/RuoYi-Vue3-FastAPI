import base from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vitest.config'
import { zxuiSourceIntegrationPlugin } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vite/zxui-theme-packages'
const root = '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend'
export default {
  ...base, root,
  plugins: [...(base.plugins ?? []), zxuiSourceIntegrationPlugin(root, '/Users/hqz/Downloads/element-plus')],
  test: { ...base.test, watch: false, reporters: ['default'], outputFile: undefined,
    include: ['tests/unit/api/cache-key.test.ts','src/utils/http.test.ts'],
  },
}
