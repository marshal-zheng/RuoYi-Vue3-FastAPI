import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

// Ship the exercised examples, not a second hand-maintained documentation copy.
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const pilot = '../../docs/research/schema-form-pilot/pilot/'
for (const file of [
  'recipes/JsonSettingsField.vue',
  'inspection/MeasurementRows.vue',
  'inspection/model.ts',
  'protocol/ProtocolConfig.vue',
]) {
  const target = resolve(root, 'dist/examples', file)
  mkdirSync(dirname(target), { recursive: true })
  copyFileSync(resolve(root, pilot, file), target)
}
writeFileSync(
  resolve(root, 'dist/README.md'),
  readFileSync(resolve(root, 'README.md'), 'utf8').replaceAll(
    pilot,
    './examples/'
  )
)
