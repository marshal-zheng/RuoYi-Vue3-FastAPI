import base from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vitest.config'
import { zxuiSourceIntegrationPlugin } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/vite/zxui-theme-packages'
const root = '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend'
export default {
  ...base, root,
  plugins: [...(base.plugins ?? []), zxuiSourceIntegrationPlugin(root, '/Users/hqz/Downloads/element-plus')],
  test: { ...base.test, watch: false, reporters: ['default'], outputFile: undefined,
    include: ['src/mocks/handlers/api-contract.test.ts', 'src/mocks/handlers/api-contract-schema.test.ts', 'src/mocks/store/datasource.test.ts','tests/unit/components/VersionCloneFeedback.test.ts', 'tests/unit/components/AuthenticatedUpload.test.ts','tests/unit/components/VersionExportDialog.test.ts','src/mocks/handlers/project.test.ts','tests/unit/components/PostSaveFeedback.test.ts','tests/unit/api/post.feedback.test.ts','src/views/system/post/components/post-form.test.ts','src/utils/http.test.ts','tests/unit/components/EditorReadLifecycle.test.ts','tests/unit/components/RemainingEditorReadLifecycle.test.ts','tests/unit/components/UserFormDialog.test.ts','tests/unit/components/DeptDlg.test.ts'],
  },
}
