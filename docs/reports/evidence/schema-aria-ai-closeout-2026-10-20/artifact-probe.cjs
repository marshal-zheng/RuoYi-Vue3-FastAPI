// Run: node artifact-probe.cjs /absolute/path/to/artifact-environment.json
const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')
const { createRequire } = require('node:module')
const { createHash } = require('node:crypto')
const environment = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))
const req = createRequire(`${environment.workspace}/package.json`)
const esbuild = req('esbuild')
const compiledEs = path.join(environment.workspace, 'compiled-es.cjs')
esbuild.buildSync({
  entryPoints: [path.join(environment.package, 'es/input-number/index.mjs')],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  packages: 'external',
  outfile: compiledEs,
  logLevel: 'silent',
})

const { Window } = req('happy-dom')
const window = new Window()
for (const key of [
  'window',
  'document',
  'navigator',
  'Element',
  'HTMLElement',
  'SVGElement',
  'Node',
  'Event',
  'FocusEvent',
  'KeyboardEvent',
  'MouseEvent',
  'MutationObserver',
]) {
  global[key] = key === 'window' ? window : window[key]
}
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
const { createSSRApp, h, nextTick, reactive } = req('vue')
const { mount, config } = req('@vue/test-utils')
const { renderToString } = req('@vue/server-renderer')
const { ElInputNumber } = req('element-plus')
config.global.stubs = { teleport: true }

function inputFromHtml(html) {
  const root = document.createElement('div')
  root.innerHTML = html
  return root.querySelector('input')
}

async function probe(Component) {
  const state = reactive({
    value: 0,
    min: -1,
    max: 3,
    disabled: false,
    attrs: {
      'aria-invalid': true,
      'aria-describedby': 'quantity-error',
      'aria-labelledby': 'quantity-label',
      class: 'quantity-layout',
      style: { width: '200px' },
    },
  })
  const wrapper = mount(
    () =>
      h(Component, {
        ...state.attrs,
        modelValue: state.value,
        min: state.min,
        max: state.max,
        disabled: state.disabled,
        step: 0.5,
        precision: 1,
        'onUpdate:modelValue': (value) => {
          state.value = value
        },
      }),
    { attachTo: document.body }
  )
  const input = wrapper.get('input')
  assert.equal(input.attributes('role'), 'spinbutton')
  assert.equal(input.attributes('aria-invalid'), 'true')
  assert.equal(input.attributes('aria-describedby'), 'quantity-error')
  assert.equal(input.attributes('aria-labelledby'), 'quantity-label')
  assert.equal(input.attributes('aria-valuenow'), '0')
  assert.equal(
    wrapper.get('.el-input-number').attributes('aria-describedby'),
    undefined
  )
  assert(wrapper.get('.el-input-number').classes().includes('quantity-layout'))
  assert(wrapper.get('.el-input-number').attributes('style').includes('200px'))
  state.attrs['aria-describedby'] = 'quantity-help'
  state.attrs['aria-invalid'] = false
  await nextTick()
  assert.equal(input.attributes('aria-describedby'), 'quantity-help')
  assert.equal(input.attributes('aria-invalid'), 'false')
  delete state.attrs['aria-describedby']
  delete state.attrs['aria-invalid']
  await nextTick()
  assert.equal(input.attributes('aria-describedby'), undefined)
  assert.equal(input.attributes('aria-invalid'), undefined)
  await input.trigger('keydown', { key: 'ArrowUp', code: 'ArrowUp' })
  assert.equal(state.value, 0.5)
  await nextTick()
  assert.equal(input.attributes('aria-valuenow'), '0.5')
  state.min = 0
  state.max = 1
  state.disabled = true
  await nextTick()
  assert.equal(input.attributes('aria-valuemin'), '0')
  assert.equal(input.attributes('aria-valuemax'), '1')
  assert.equal(input.attributes('aria-disabled'), 'true')
  await input.trigger('keydown', { key: 'ArrowUp', code: 'ArrowUp' })
  assert.equal(state.value, 0.5)
  wrapper.unmount()

  const html = await renderToString(
    createSSRApp({
      render: () =>
        h(Component, {
          modelValue: 0,
          name: 'quantity',
          min: -2,
          max: 5,
          'aria-invalid': true,
          'aria-describedby': 'quantity-error',
        }),
    })
  )
  const ssrInput = inputFromHtml(html)
  for (const [key, value] of Object.entries({
    role: 'spinbutton',
    name: 'quantity',
    'aria-invalid': 'true',
    'aria-describedby': 'quantity-error',
    'aria-valuenow': '0',
    'aria-valuemin': '-2',
    'aria-valuemax': '5',
  })) {
    assert.equal(ssrInput.getAttribute(key), value)
  }
  return {
    passed: true,
    checks: [
      'native ARIA on actual input; layout attrs on root',
      'dynamic native attrs update and removal',
      'keyboard stepping retains numeric semantics',
      'reactive min/max/disabled ARIA and disabled stepping',
      'SSR spinbutton ARIA, name and error-description relation',
    ],
    ssrInputHtml: ssrInput.outerHTML,
  }
}

;(async () => {
  const result = {
    capturedAt: new Date().toISOString(),
    scope: 'Packed public leaf against copied stock npm EP 2.13; happy-dom and SSR',
    environment,
    versions: {
      vue: req('vue').version,
      elementPlus: req('element-plus').version,
      esbuild: esbuild.version,
    },
    esmMethod:
      'ES leaf from extracted tarball bundled for Node SSR with existing esbuild; public dependencies external',
    nativeNodeEsmLimitation:
      'Direct upstream EP ESM import fails on @popperjs/core placements CommonJS named-export interop; no package source is patched',
    license: {},
    formats: {},
  }
  const originalHtml = await renderToString(
    createSSRApp({
      render: () =>
        h(ElInputNumber, {
          modelValue: 0,
          'aria-invalid': true,
          'aria-describedby': 'quantity-error',
        }),
    })
  )
  const originalInput = inputFromHtml(originalHtml)
  assert.equal(originalInput.getAttribute('aria-invalid'), null)
  assert.equal(originalInput.getAttribute('aria-describedby'), null)
  result.stockPeerControl = {
    reproducedOriginalMissingAria: true,
    inputHtml: originalInput.outerHTML,
  }
  for (const [format, relativePath] of [
    ['ES', 'es/components/input-number/src/number-control.vue.mjs'],
    ['CJS', 'lib/components/input-number/src/number-control.vue.js'],
  ]) {
    const content = fs.readFileSync(
      path.join(environment.package, relativePath),
      'utf8'
    )
    assert(content.includes('MIT License'))
    assert(content.includes('Copyright (c) 2020-PRESENT Element Plus'))
    assert(content.includes('Permission is hereby granted, free of charge'))
    assert(content.includes('THE SOFTWARE IS PROVIDED "AS IS"'))
    result.license[format] = {
      completeNoticeRetained: true,
      file: relativePath,
      sha256: createHash('sha256').update(content).digest('hex'),
    }
  }
  result.formats.CJS = await probe(req('@zxio/zxui/input-number').ZxInputNumber)
  result.formats.ES = await probe(req(compiledEs).ZxInputNumber)
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
})().catch((error) => {
  process.stderr.write(`${error.stack}\n`)
  process.exitCode = 1
})
