import base from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vitest.config'
import { zxuiSourceIntegrationPlugin } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vite/zxui-theme-packages'
const root = '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend'
export default {
  ...base, root,
  plugins: [...(base.plugins ?? []), zxuiSourceIntegrationPlugin(root, '/Users/hqz/Downloads/element-plus')],
  test: { ...base.test, watch: false, reporters: ['default'], outputFile: undefined,
    include: ['tests/unit/components/AuthenticatedUpload.test.ts','tests/unit/components/WebSocketSession.test.ts','tests/unit/components/UserImportDialog.test.ts','src/plugins/dev-menu-hot-sync.test.ts','src/utils/session.test.ts','src/utils/io-toolkit/upload.contract.test.ts','src/utils/http.test.ts','src/store/modules/user.login.test.ts'],
  },
}
