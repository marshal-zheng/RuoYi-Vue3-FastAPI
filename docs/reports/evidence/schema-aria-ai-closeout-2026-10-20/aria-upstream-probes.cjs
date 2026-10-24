// Run: node aria-upstream-probes.cjs [/path/to/zxui] > aria-upstream-probes.json
// No ZXUI component is loaded: these are direct Element Plus controls.
const { createRequire } = require('node:module')
const zxuiRoot = process.argv[2] || '/Users/hqz/Downloads/element-plus'
const req = createRequire(`${zxuiRoot}/package.json`)
const epReq = createRequire(`${zxuiRoot}/packages/components/package.json`)
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
  'MutationObserver',
]) {
  global[key] = key === 'window' ? window : window[key]
}
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
const { createSSRApp, h, reactive, nextTick } = req('vue')
const { mount, config, flushPromises } = req('@vue/test-utils')
const { renderToString } = req('@vue/server-renderer')
const ep = epReq('element-plus')
config.global.stubs = { teleport: true }

async function checkUnmount(Component, withLayoutDiv) {
  const disabled = reactive({ value: false })
  const form = () =>
    h(ep.ElForm, { disabled: disabled.value }, () =>
      h(ep.ElFormItem, { label: 'Quantity' }, () =>
        h(Component, { modelValue: 1 })
      )
    )
  const wrapper = mount(() =>
    h(ep.ElConfigProvider, { size: 'large' }, () =>
      withLayoutDiv ? h('div', [form()]) : form()
    )
  )
  await nextTick()
  disabled.value = true
  await nextTick()
  await flushPromises()
  await nextTick()
  const input = wrapper.get('input')
  const result = {
    component: Component.name,
    fixture: withLayoutDiv
      ? 'ConfigProvider > div > Form > FormItem > control'
      : 'ConfigProvider > Form > FormItem > control',
    flushedPromisesBeforeUnmount: true,
    labelMatchesInput:
      wrapper.get('label').attributes('for') === input.attributes('id'),
    inheritedDisabled: input.attributes('disabled') === '',
  }
  try {
    wrapper.unmount()
    result.unmountPassed = true
  } catch (error) {
    result.unmountPassed = false
    result.error = error.message
    result.stack = error.stack.split('\n').slice(0, 7)
  }
  return result
}

async function checkSsr(Component) {
  const html = await renderToString(
    createSSRApp({
      render: () =>
        h(Component, {
          id: 'quantity',
          name: 'quantity',
          modelValue: 0,
          'aria-label': 'Quantity',
          'aria-describedby': 'quantity-error',
        }),
    })
  )
  const root = document.createElement('div')
  root.innerHTML = html
  const input = root.querySelector('input')
  return {
    component: Component.name,
    requestedId: 'quantity',
    actualInputId: input?.getAttribute('id') ?? null,
    actualInputName: input?.getAttribute('name') ?? null,
    inputHtml: input?.outerHTML ?? null,
  }
}

;(async () => {
  const result = {
    capturedAt: new Date().toISOString(),
    scope: 'Node + happy-dom in-memory probes; no browser or ZXUI component',
    versions: {
      node: process.version,
      vue: req('vue').version,
      elementPlus: ep.version,
    },
    unmount: [],
    ssr: [],
    interpretation: [
      'Both direct upstream controls reproduce the adjacent Provider/Form unmount error.',
      'An ordinary layout div retains provider/form inheritance and permits unmount.',
      'Explicit ElInput/ElInputNumber ids are absent in upstream SSR; their input-id hook initializes onMounted.',
      'These are upstream/test-fixture observations, not evidence of a browser failure.',
    ],
  }
  for (const Component of [ep.ElInputNumber, ep.ElInput]) {
    result.unmount.push(await checkUnmount(Component, false))
    result.unmount.push(await checkUnmount(Component, true))
    result.ssr.push(await checkSsr(Component))
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
})().catch((error) => {
  process.stderr.write(`${error.stack}\n`)
  process.exitCode = 1
})
