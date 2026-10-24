const fs = require('node:fs')
const path = require('node:path')
const root = '/Users/hqz/dev/RuoYi-Vue3-FastAPI'
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'baseline-manifest.json'), 'utf8'))
const mapping = Object.fromEntries(Object.keys(manifest).map(p => [path.join(root, p), path.join(__dirname, 'baseline', p)]))
const fresh = ['src/composables/useAuthenticatedUpload.ts','src/composables/useUploadModel.ts','tests/unit/components/AuthenticatedUpload.test.ts','tests/unit/components/WebSocketSession.test.ts']
const originalRead = fs.readFileSync
fs.readFileSync = function(file, ...args) {
  if (fresh.some(p => String(file) === path.join(root, 'ruoyi-fastapi-frontend', p))) return 'export {}'
  return originalRead.call(this, mapping[String(file)] ?? file, ...args)
}
