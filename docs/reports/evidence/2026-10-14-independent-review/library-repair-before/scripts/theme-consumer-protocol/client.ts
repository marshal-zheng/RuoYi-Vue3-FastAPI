/* eslint-disable no-console -- The isolated browser fixture emits verification diagnostics. */
import { createApp, createSSRApp, nextTick } from 'vue'
import { createDefaultBrowserThemeHost } from '@zxio/zxui/theme-host'
import { createThemeAssetResolver, success } from '@zxio/zxui/theme-runtime'
import { Widget as StandaloneWidget } from '@acme/widget/vue'
import data from 'virtual:consumer-fixture'
import { createConsumerDemo } from './app'
import '@acme/widget/style.css'
import '@example/panel/style.css'

const browser = window as any
const initial = browser.__CONSUMER_SSR__
const demo = createConsumerDemo(initial?.initial)
const standalone = new URL(location.href).searchParams.has('standalone')
const app = standalone
  ? createApp(StandaloneWidget, { label: 'standalone' })
  : initial
  ? createSSRApp(demo.Root)
  : createApp(demo.Root)
const warnings: string[] = []
app.config.warnHandler = (message) => {
  warnings.push(message)
  console.warn(message)
}
const errors: string[] = []
app.config.errorHandler = (error) => {
  errors.push(String(error))
  console.error(error)
}
const result = standalone
  ? null
  : createDefaultBrowserThemeHost({
      appKey: 'consumer-browser',
      themes: data.themes.map((manifest: unknown) => ({ manifest })),
      defaultThemeId: 'default',
      extensions: data.bundles,
      seedPolicy: { allow: ['brand'] },
      systemPreference: {
        currentMode: () => 'light',
        subscribe: () => () => undefined,
      },
      assetResolver: createThemeAssetResolver({
        exports: {
          async resolve(input) {
            const response = await fetch(
              `/theme-asset?package=${encodeURIComponent(
                input.packageName
              )}&export=${encodeURIComponent(input.exportPath)}`
            )
            return success({ kind: 'css-text', text: await response.text() })
          },
        },
      }),
      ...(initial
        ? {
            hydration: {
              snapshot: initial.output.snapshot,
              stylesheetElements: [
                ...document.querySelectorAll<HTMLElement>(
                  '[data-zx-theme-artifact]'
                ),
              ],
              stylesheetOwnership: 'transferred' as const,
              manualCompletion: true,
              consumers: initial.output.consumers,
              ...(initial.initial.customPortal
                ? { consumerPortalRoots: { aux: document.body } }
                : {}),
              composition: {
                snapshot: initial.output.composition,
                scopeElements: [
                  ...document.querySelectorAll<HTMLElement>('.provider-root'),
                ],
                styleElements: [
                  ...document.querySelectorAll<HTMLElement>(
                    '[data-zx-composition-style]'
                  ),
                ],
                ownership: 'transferred' as const,
              },
            },
          }
        : {}),
    })
const api = (browser.__CONSUMER__ = {
  state: demo.state,
  warnings,
  errors,
  error: null as unknown,
  host: result?.ok ? result.value : null,
  complete: null as unknown,
  async unmount() {
    app.unmount()
    if (result?.ok) await result.value.dispose()
  },
  async settle() {
    await nextTick()
    await nextTick()
  },
})
if (result && !result.ok) api.error = result.diagnostics
else if (standalone) {
  app.mount('#app')
} else {
  const bound = result!.value.bind(app)
  if (!bound.ok) api.error = bound.diagnostics
  else {
    const nodes = [...document.querySelectorAll('[data-zx-consumer]')]
    const styles = [...document.querySelectorAll('style')]
    app.mount('#app')
    await nextTick()
    await nextTick()
    if (initial) {
      const complete = bound.value.completeHydration()
      api.complete = complete
      if (!complete.ok) api.error = complete.diagnostics
      else {
        browser.__CONSUMER_REUSED__ = {
          nodes: nodes.every((node) => node.isConnected),
          styles: styles.every((style) => style.isConnected),
        }
      }
    }
  }
}
