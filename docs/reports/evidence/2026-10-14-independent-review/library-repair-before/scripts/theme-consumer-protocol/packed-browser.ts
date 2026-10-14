/* eslint-disable vue/one-component-per-file -- This harness creates independent owner/portal fixture components. */
import {
  Teleport,
  createApp,
  defineComponent,
  h,
  nextTick,
  ref,
  withDirectives,
} from 'vue'
import {
  themeConsumerDiscoveryKey,
  themeConsumerScopeKey,
} from '@zxio/theme-consumer'
import { useThemePortalBinding } from '@zxio/theme-consumer/vue'
// A second installed tarball, CJS entry. No source module or alias participates.
import { useThemeCssAdapter } from './node_modules/consumer-copy-b/dist/cjs/vue/index.cjs'
import { Widget as Acme } from '@acme/widget/vue'
import { Widget as Panel } from '@example/panel/vue'
import '@acme/widget/style.css'
import '@example/panel/style.css'

const check = (condition: unknown, message: string) => {
  if (!condition) throw new Error(message)
}
const run = async () => {
  const standalone = createApp(
    defineComponent({
      setup: () => () =>
        h('main', [h(Acme, { label: 'a' }), h(Panel, { label: 'b' })]),
    })
  )
  standalone.mount('#app')
  await nextTick()
  check(
    document.querySelectorAll('[data-consumer-status="standalone"]').length ===
      2,
    'both ordinary UIs are standalone'
  )
  const button = document.querySelector('button')!
  button.click()
  await nextTick()
  check(
    button.textContent?.includes('1'),
    'core interaction remains functional'
  )
  standalone.unmount()
  const events: string[] = [],
    listeners = new Set<() => void>()
  const active = ref(true)
  let portal: ReturnType<typeof useThemePortalBinding>
  const abi = { major: 1, minor: 0, capabilities: ['css-target', 'portal'] }
  const port = {
    abi,
    snapshot: () => ({
      phase: 'ready',
      ownerToken: 'host-owner',
      revision: 1,
      diagnostics: [],
    }),
    subscribe(listener: () => void) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    preparePortal: () => ({ ok: true, value: null, diagnostics: [] }),
    async acquirePortal() {
      events.push('acquire-portal')
      const target = document.body.appendChild(document.createElement('aside'))
      return {
        ok: true,
        diagnostics: [],
        value: {
          snapshot: () => ({
            state: 'ready',
            target,
            leaseId: 'cross-copy-portal',
            diagnostics: [],
          }),
          subscribe: () => () => undefined,
          release() {
            check(
              !target.querySelector('[data-bound]'),
              'content must release before portal'
            )
            events.push('release-portal')
            target.remove()
          },
        },
      }
    },
    async bindCssTarget(element: HTMLElement, input: any) {
      check(
        input.portalLeaseId === 'cross-copy-portal',
        'cross-copy structural association'
      )
      element.dataset.bound = 'yes'
      events.push('bind-css')
      return {
        ok: true,
        diagnostics: [],
        value: {
          snapshot: () => ({ state: 'ready', diagnostics: [] }),
          subscribe: () => () => undefined,
          release() {
            delete element.dataset.bound
            events.push('release-css')
          },
        },
      }
    },
  }
  const Consumer = defineComponent({
    setup() {
      portal = useThemePortalBinding({ active })
      const root = ref<HTMLElement | null>(null)
      const css = useThemeCssAdapter(
        root,
        { id: 'cross', actualVersion: '1.0.0' },
        { portal }
      )
      return () =>
        active.value && portal.target.value
          ? h(Teleport, { to: portal.target.value }, [
              withDirectives(h('div', { ref: root }, 'cross-copy'), [
                [css.directive],
              ]),
            ])
          : null
    },
  })
  const app = createApp(Consumer)
  app.provide(themeConsumerDiscoveryKey, {
    schema: 'zx.theme-consumer.discovery/1',
    abis: [abi],
  })
  app.provide(themeConsumerScopeKey, port)
  app.mount('#app')
  for (let i = 0; i < 5; i++) await nextTick()
  check(document.querySelector('[data-bound]'), 'portal content mounted')
  active.value = false
  for (let i = 0; i < 5; i++) await nextTick()
  check(
    events.indexOf('release-css') < events.indexOf('release-portal'),
    'release barrier'
  )
  app.unmount()
  await nextTick()
  check(
    listeners.size === 0 && !document.querySelector('aside'),
    'all resources released'
  )
  return {
    status: 'pass',
    copies: ['ESM A portal', 'CJS B CSS'],
    events,
    standalone: 2,
    subscriptionsAfterDispose: listeners.size,
  }
}
run().then(
  (result) => {
    ;(window as any).__PACKED__ = result
  },
  (error) => {
    ;(window as any).__PACKED__ = { status: 'fail', error: String(error) }
    throw error
  }
)
