/* eslint-disable no-console -- The local validation runner reports its bounded result. */
import { spawnSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const workspace = resolve(import.meta.dirname, '../..')
const source = spawnSync(
  process.execPath,
  [resolve(workspace, 'scripts/ai-production-hardening/source-closure.mjs')],
  { cwd: workspace, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }
)
const closure = JSON.parse(source.stdout)
const bound = closure.repositories.filter(
  (repository) => repository.role === 'bound'
)
if (
  source.error ||
  ![0, 2].includes(source.status) ||
  closure.kind !== 'zx.ai.production.source-closure.v1' ||
  !/^sha256:[a-f0-9]{64}$/.test(closure.fingerprint) ||
  bound.some((repository) => !/^[a-f0-9]{40}$/.test(repository.commit ?? '')) ||
  (source.status === 2 &&
    !bound.some((repository) => repository.clean === false))
) {
  throw new Error('local-authority-source-closure-invalid')
}

// Local tests accept recorded working changes. The release runner still
// requires its original clean commit set; this result is never release evidence.
const result = spawnSync(
  process.execPath,
  [
    resolve(
      workspace,
      'scripts/ai-production-hardening/workbench-authority-observation.mjs'
    ),
    closure.fingerprint,
  ],
  {
    cwd: workspace,
    encoding: 'utf8',
    timeout: 300_000,
    maxBuffer: 64 * 1024 * 1024,
  }
)
const observation = JSON.parse(result.stdout)
if (result.error || result.status !== 0 || observation.valid !== true) {
  process.stderr.write(result.stderr)
  throw new Error('local-authority-observation-failed')
}
const evidence = process.env.ZXUI_VALIDATION_EVIDENCE_DIR
if (evidence) {
  mkdirSync(evidence, { recursive: true })
  writeFileSync(resolve(evidence, 'source-closure.json'), source.stdout)
  writeFileSync(resolve(evidence, 'authority-observation.json'), result.stdout)
}
console.log(
  JSON.stringify({
    scope: 'local-working-source-validation',
    sourceClosureFingerprint: closure.fingerprint,
    rootClean: closure.root.clean,
    personas: observation.personas,
    stages: observation.stages.length,
    valid: observation.valid,
  })
)
