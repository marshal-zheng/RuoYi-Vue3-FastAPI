#!/usr/bin/env node
/* Frozen output evaluator. No generated source is repaired. See README.md. */
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const cp = require('node:child_process')
const { createRequire } = require('node:module')
const assert = require('node:assert/strict')
const crypto = require('node:crypto')

const args = Object.fromEntries(process.argv.slice(2).map((arg) => {
  const at = arg.indexOf('=')
  if (at < 0) throw new Error(`Expected --name=value: ${arg}`)
  return [arg.slice(2, at), arg.slice(at + 1)]
}))
for (const key of ['output', 'artifact', 'variant', 'domain', 'zxui', 'formcreate', 'result'])
  if (!args[key]) throw new Error(`Missing --${key}=...`)
if (!['baseline', 'current'].includes(args.variant)) throw new Error('Invalid variant')
const zxui = path.resolve(args.zxui)
const requireZx = createRequire(path.join(zxui, 'package.json'))
const ts = requireZx('typescript')
const esbuild = createRequire(requireZx.resolve('vite/package.json'))('esbuild')
const artifact = path.resolve(args.artifact)
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'schema-author-quality-'))
fs.symlinkSync(path.join(zxui, 'node_modules'), path.join(work, 'node_modules'), 'dir')
const checks = []
const failures = []
const record = async (name, run) => {
  try { await run(); checks.push({ name, passed: true }) }
  catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    checks.push({ name, passed: false, error: message })
    failures.push(name)
  }
}
const hash = (data) => crypto.createHash('sha256').update(data).digest('hex')
let generated
let source = ''
let vueSource = ''
let rules
let mod
let mounted
let testWindow
const knownFields = ['postName', 'postCode', 'postSort', 'status', 'remark']
const valid = { postName: '岗位 A', postCode: 'role_a', postSort: 0, status: '0', remark: '备注' }
const invalid = [
  ['name-whitespace', { postName: ' \t\n' }],
  ['name-too-long', { postName: 'x'.repeat(51) }],
  ['code-whitespace', { postCode: ' \t\n' }],
  ['code-too-long', { postCode: 'x'.repeat(65) }],
  ['sort-negative', { postSort: -1 }],
  ['sort-fractional', { postSort: 0.5 }],
  ['sort-nan', { postSort: Number.NaN }],
  ['sort-infinite', { postSort: Infinity }],
  ['sort-string', { postSort: '0' }],
  ['status-unknown', { status: '2' }],
  ['remark-not-string', { remark: 123 }],
]

async function main() {
  // Establish the memory DOM before any authored runtime import can load Vue.
  const { Window } = requireZx('happy-dom')
  testWindow = new Window()
  for (const key of ['window', 'document', 'navigator', 'HTMLElement', 'Element', 'SVGElement', 'Node', 'HTMLInputElement', 'Event', 'CustomEvent'])
    Object.defineProperty(globalThis, key, { value: key === 'window' ? testWindow : testWindow[key], configurable: true, writable: true })
  await record('structured-output', () => {
    generated = JSON.parse(fs.readFileSync(args.output, 'utf8'))
    assert.deepEqual(Object.keys(generated).sort(), ['postEditorVue', 'postFormTs'])
    assert.equal(typeof generated.postFormTs, 'string')
    assert.equal(typeof generated.postEditorVue, 'string')
    assert(generated.postFormTs.trim() && generated.postEditorVue.trim())
    source = generated.postFormTs
    vueSource = generated.postEditorVue
    fs.writeFileSync(path.join(work, 'post-form.ts'), source)
    fs.writeFileSync(path.join(work, 'PostEditor.vue'), vueSource)
    fs.copyFileSync(args.domain, path.join(work, 'domain.ts'))
  })
  if (!source || !vueSource) return
  await record('no-type-escape', () => {
    const snippets = [source, ...[...vueSource.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map((match) => match[1])]
    for (const text of snippets) {
      const file = ts.createSourceFile('authored.ts', text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
      const visit = (node) => {
        assert.notEqual(node.kind, ts.SyntaxKind.AnyKeyword, 'Generated source contains explicit any')
        ts.forEachChild(node, visit)
      }
      visit(file)
      assert(!/@ts-(?:ignore|nocheck|expect-error)\b/.test(text), 'Generated source suppresses type diagnostics')
      assert(!/\bas\s+unknown\s+as\b/.test(text), 'Generated source uses as unknown as')
    }
  })
  await record('public-types-and-field-keys', () => {
    // These are each variant's real emitted declarations, not synthetic common types.
    const paths = {
      '@zxio/schema-form': [path.join(artifact, 'index.d.ts')],
      '@zxio/schema-form/form-create': [path.join(artifact, 'form-create/index.d.ts')],
      '@zxio/schema-form/fields': [path.join(artifact, 'fields/index.d.ts')],
      '@form-create/element-ui': [path.join(path.resolve(args.formcreate), 'types/index.d.ts')],
      vue: [path.join(zxui, 'node_modules/vue/dist/vue.d.ts')],
    }
    const contract = `
import { createPostRules, toPostDto, postFieldIssues, createPostSave } from './post-form'
import type { PostApi, PostValues, PostDto, ServerIssue } from './domain'
import type { FieldIssue } from '@zxio/schema-form/form-create'
type Assert<T extends true> = T
type Fields = ReturnType<typeof createPostRules>[number]['field']
type FieldsAreChecked = Assert<Exclude<Fields, keyof PostValues> extends never ? true : false>
declare const values: PostValues
declare const api: PostApi
declare const issues: readonly ServerIssue[]
const dto: PostDto = toPostDto({ ...values }, 11)
const mapped: readonly FieldIssue[] = postFieldIssues(issues)
const save = createPostSave(api, 11)
save({ ...values }, new AbortController().signal)
export type { FieldsAreChecked }
export { dto, mapped }
`
    fs.writeFileSync(path.join(work, 'author-contract.ts'), contract)
    fs.writeFileSync(path.join(work, 'env.d.ts'), "declare module '*.css' {}\n")
    fs.writeFileSync(path.join(work, 'tsconfig.json'), JSON.stringify({
      compilerOptions: {
        target: 'ES2022', module: 'ESNext', moduleResolution: 'Bundler',
        strict: true, skipLibCheck: true, noEmit: true, esModuleInterop: true,
        allowSyntheticDefaultImports: true, lib: ['ES2022', 'DOM'],
        baseUrl: work, paths, types: [],
      },
      include: ['*.ts', '*.vue'],
    }, null, 2))
    const result = cp.spawnSync(path.join(zxui, 'node_modules/.bin/vue-tsc'), ['-p', path.join(work, 'tsconfig.json'), '--noEmit'], { encoding: 'utf8', timeout: 120000 })
    fs.writeFileSync(path.join(work, 'typecheck.log'), `${result.stdout ?? ''}${result.stderr ?? ''}`)
    assert.equal(result.status, 0, `${result.stdout ?? ''}${result.stderr ?? ''}`.trim() || `vue-tsc exit ${result.status}`)
  })
  await record('load-unaltered-domain-module', () => {
    const transformed = esbuild.transformSync(source, { loader: 'ts', format: 'cjs', target: 'node22', sourcefile: 'post-form.ts' }).code
    const localModule = { exports: {} }
    const localRequire = (specifier) => {
      if (specifier === 'vue') return requireZx('vue')
      if (specifier === '@zxio/schema-form') return require(path.join(artifact, 'index.cjs'))
      throw new Error(`Unsupported runtime import in pure business adapter: ${specifier}; inspect before extending evaluator`)
    }
    new Function('require', 'module', 'exports', transformed)(localRequire, localModule, localModule.exports)
    mod = localModule.exports
    for (const key of ['createPostRules', 'toPostDto', 'postFieldIssues', 'createPostSave'])
      assert.equal(typeof mod[key], 'function', `Missing function ${key}`)
  })
  if (mod) {
    await record('dto-whitelist-and-trusted-identity', () => {
      const poisoned = { ...valid, postId: 999, administrative: true, unknown: 'discard' }
      const before = structuredClone(poisoned)
      assert.deepEqual(mod.toPostDto(poisoned), valid)
      assert.deepEqual(mod.toPostDto(poisoned, 0), { ...valid, postId: 0 })
      assert.deepEqual(mod.toPostDto(poisoned, 71), { ...valid, postId: 71 })
      assert.deepEqual(poisoned, before)
      assert.deepEqual(mod.toPostDto({ ...valid, status: '1', postSort: 5 }), { ...valid, status: '1', postSort: 5 })
    })
    for (const [name, patch] of invalid)
      await record(`dto-rejects-${name}`, () => assert.throws(() => mod.toPostDto({ ...valid, ...patch })))
    await record('server-issues-known-and-summary', () => {
      const fields = ['post_name', 'post_code', 'post_sort', 'status', 'remark', 'unknown_backend_field', '', '__proto__', 'constructor', 'toString']
      const errors = fields.map((field, index) => ({ field, message: `error-${index}` }))
      const mapped = mod.postFieldIssues(errors)
      assert.equal(mapped.length, errors.length)
      mapped.forEach((issue, index) => {
        assert.equal(issue.message, errors[index].message)
        if (args.variant === 'baseline') {
          assert.equal(typeof issue.field, 'string')
          if (index < 5) assert.equal(issue.field, knownFields[index])
          else assert(!knownFields.includes(issue.field), 'Unknown server issue points to a known field')
        } else if (index < 5) assert.deepEqual(issue.path, [knownFields[index]])
        else {
          assert(!issue.path?.length || !knownFields.includes(issue.path[0]), 'Unknown server issue points to a known field')
          assert(!issue.path || (Array.isArray(issue.path) && issue.path.every((part) => typeof part === 'string' || typeof part === 'number')), 'Unknown server issue has an invalid field path')
        }
      })
    })
    await record('save-signal-dto-success-and-failure', async () => {
      const signal = new AbortController().signal
      const calls = []
      let response = { ok: true }
      const api = { write: async (dto, passedSignal) => { calls.push({ dto, signal: passedSignal }); return response } }
      const save = mod.createPostSave(api, 71)
      assert.deepEqual(await save({ ...valid, postId: 999, extra: 'ignore' }, signal), { ok: true })
      assert.equal(calls.length, 1)
      assert.deepEqual(calls[0].dto, { ...valid, postId: 71 })
      assert.equal(calls[0].signal, signal)
      response = { ok: false, errors: [{ field: 'post_name', message: 'already exists' }, { field: '', message: 'conflict' }] }
      assert.deepEqual(await save(valid, signal), { ok: false, issues: mod.postFieldIssues(response.errors) })
      assert.equal(calls.length, 2)
      assert.equal(calls[1].signal, signal)
    })
    await record('rules-own-exact-five-fields-no-initial-values', () => {
      rules = mod.createPostRules()
      assert(Array.isArray(rules))
      assert.deepEqual(rules.map((rule) => rule.field).sort(), [...knownFields].sort())
      assert(rules.every((rule) => !Object.hasOwn(rule, 'value')), 'Rule.value creates a second initial baseline')
      assert.equal(rules.find((rule) => rule.field === 'remark')?.props?.type, 'textarea')
    })
    if (rules) {
      const requireComponents = createRequire(path.join(zxui, 'packages/components/package.json'))
      const AV = createRequire(requireComponents.resolve('element-plus/package.json'))('async-validator')
      const Validator = AV.default ?? AV
      const descriptor = Object.fromEntries(rules.map((rule) => [rule.field, rule.validate ?? []]))
      const validator = new Validator(descriptor)
      await record('rules-accept-valid-zero', () => validator.validate(valid))
      for (const [name, patch] of invalid.filter(([name]) => !['sort-nan', 'sort-infinite', 'remark-not-string'].includes(name)))
        await record(`rules-reject-${name}`, async () => {
          let rejected = false
          try { await validator.validate({ ...valid, ...patch }) } catch { rejected = true }
          assert(rejected, `Native validation accepted ${name}`)
        })
    }
  }
  await record('editor-public-contract-and-style', () => {
    assert(/<script\b(?=[^>]*\bsetup\b)(?=[^>]*\blang=["']ts["'])/.test(vueSource), 'Editor must use script setup lang=ts')
    assert(/@zxio\/schema-form\/style\.css/.test(vueSource), 'Missing public style import')
    assert(/\bSchemaFormInstance\b/.test(vueSource), 'Missing public form instance type')
    assert(!/<ZxSchemaForm\b[^>]*\bv-model(?=[\s:=.>])/.test(vueSource), 'SchemaForm must own editing values')
  })
  if (mod && rules) {
    await record('editor-one-session-actions-pending-and-layout', async () => {
      // Happy DOM + a schema API stub checks authored wiring. It does not claim
      // browser or engine integration coverage; the package has separate tests.
      const vue = requireZx('vue')
      const { mount } = requireZx('@vue/test-utils')
      const compiler = createRequire(requireZx.resolve('vue/package.json'))('@vue/compiler-sfc')
      const pending = vue.ref(false)
      const invocations = { submit: 0, reset: 0, initialize: 0 }
      const observed = []
      const SchemaStub = vue.defineComponent({
        name: 'ZxSchemaForm',
        props: ['initial', 'createRules', 'save', 'columns'],
        setup(props, { expose, attrs }) {
          invocations.initialize++
          assert.equal(typeof props.createRules, 'function')
          assert.equal(typeof props.save, 'function')
          props.createRules({ read: () => structuredClone(valid), signal: () => new AbortController().signal })
          expose({
            pending, dirty: false, blocked: false,
            submit: async () => { invocations.submit++; return true },
            reset: () => { invocations.reset++ },
          })
          return () => {
            observed.push({ initial: props.initial, rules: props.createRules, save: props.save, columns: props.columns, attrs: { ...attrs } })
            return vue.h('section')
          }
        },
      })
      const { descriptor } = compiler.parse(vueSource)
      const script = compiler.compileScript(descriptor, { id: 'schema-author-sample', inlineTemplate: true })
      const js = esbuild.transformSync(script.content, { loader: 'ts', format: 'cjs', target: 'node22' }).code
      const editorModule = { exports: {} }
      const localRequire = (specifier) => {
        if (specifier === 'vue') return vue
        if (specifier === './post-form' || specifier === './post-form.ts') return mod
        if (specifier === '@zxio/schema-form/form-create') return { ZxSchemaForm: SchemaStub }
        if (specifier === '@zxio/schema-form/style.css') return {}
        throw new Error(`Unsupported editor runtime import: ${specifier}`)
      }
      new Function('require', 'module', 'exports', js)(localRequire, editorModule, editorModule.exports)
      mounted = mount(editorModule.exports.default, { props: { initial: valid, postId: 71, api: { write: async () => ({ ok: true }) } } })
      await vue.nextTick()
      const buttons = mounted.findAll('button')
      const saveButton = buttons.find((button) => /保存/.test(button.text()))
      const resetButton = buttons.find((button) => /恢复/.test(button.text()))
      assert(saveButton && resetButton, 'Missing save/reset buttons')
      await saveButton.trigger('click')
      await resetButton.trigger('click')
      assert.deepEqual(invocations, { submit: 1, reset: 1, initialize: 1 })
      pending.value = true
      await vue.nextTick()
      assert.equal(saveButton.element.disabled, true)
      assert.equal(resetButton.element.disabled, true)
      pending.value = false
      await vue.nextTick()
      assert.equal(saveButton.element.disabled, false)
      assert.equal(resetButton.element.disabled, false)
      assert.equal(invocations.initialize, 1)
      assert.deepEqual(observed[0].initial, valid)
      assert(observed.every((entry) => entry.rules === observed[0].rules && entry.save === observed[0].save), 'Session functions recreated on rerender')
      assert(observed.every((entry) => !Object.hasOwn(entry.attrs, 'modelValue') && !Object.hasOwn(entry.attrs, 'onUpdate:modelValue')), 'Second writable form model')
      const cols = observed[0].columns
      const span = (col, size) => {
        // ElCol responsive classes use min-width media queries: a md span
        // remains active at lg/xl unless a later breakpoint overrides it.
        let active = col?.span
        for (const breakpoint of ['xs', 'sm', 'md', 'lg', 'xl']) {
          const value = col?.[breakpoint]
          const next = typeof value === 'object' ? value?.span : value
          if (next !== undefined) active = next
          if (breakpoint === size) break
        }
        return active
      }
      for (const rule of rules) {
        if (rule.field === 'remark')
          assert(rule.fullWidth === true || ['xs', 'sm', 'md', 'lg'].every((size) => span(rule.col, size) === 24), 'Remark is not full width')
        else
          assert(cols === 2 || (span(rule.col, 'xs') === 24 && ['md', 'lg'].every((size) => span(rule.col, size) === 12)), 'Field lacks responsive one/two column layout')
      }
      mounted.unmount()
      mounted = undefined
      await testWindow.happyDOM.abort()
    })
  }
}

main().catch((error) => {
  failures.push('evaluator-infrastructure')
  checks.push({ name: 'evaluator-infrastructure', passed: false, error: error.stack ?? String(error) })
}).finally(() => {
  try { mounted?.unmount() } catch {}
  const report = {
    variant: args.variant,
    artifact,
    output: path.resolve(args.output),
    sourceSha256: source ? hash(source) : null,
    editorSha256: vueSource ? hash(vueSource) : null,
    passed: failures.length === 0,
    checksPassed: checks.filter((check) => check.passed).length,
    checksTotal: checks.length,
    failures,
    checks,
    workDirectory: work,
    scope: 'Unmodified emitted source: real per-variant public declarations; pure DTO/native validation; Happy DOM authored SFC wiring with public schema API stub. Not browser or full engine integration.',
  }
  fs.writeFileSync(args.result, JSON.stringify(report, null, 2) + '\n')
  process.stdout.write(JSON.stringify({ passed: report.passed, checksPassed: report.checksPassed, checksTotal: report.checksTotal, failures, result: path.resolve(args.result), workDirectory: work }) + '\n')
  process.exitCode = report.passed ? 0 : 1
})
