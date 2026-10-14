import assert from 'node:assert/strict'
import { mkdirSync, readFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { mkdir, writeFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { build, createServer, optimizeDeps, resolveConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { aliases } from './vite-aliases.mts'
import { buildFixtures, fixtureNames, fixtureRoot } from './build-fixtures.mts'
import { captureSsrFrame, inspectRetainedFrame } from './browser-frame.mts'
import { openGateBrowser } from './gate-browser.mts'
import { currentBaseline } from './baselines-registry.mts'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const output = resolve(
  root,
  'docs/specs/THEME-theme-consumer-protocol/evidence'
)
const loadPackage = createRequire(import.meta.url)
const { sealConsumerSnapshot } = loadPackage(
  '../../packages/zxui/theme-runtime/consumer-contract'
)
await mkdir(output, { recursive: true })
const baseline = process.argv.includes('--baseline')
let bundleRoot = fixtureRoot
if (baseline) {
  // Generation 1 predates contract 4.4 and is rejected by the current core.
  const frozen = currentBaseline.directory
  const manifest = JSON.parse(
    readFileSync(resolve(frozen, 'manifest.json'), 'utf8')
  )
  bundleRoot = resolve(root, 'node_modules/.consumer-baselines')
  for (const [index, artifact] of manifest.artifacts.entries()) {
    const tarball = resolve(frozen, artifact.file)
    assert.equal(
      `sha256:${createHash('sha256')
        .update(readFileSync(tarball))
        .digest('hex')}`,
      artifact.sha256
    )
    const directory = resolve(bundleRoot, fixtureNames[index]!)
    mkdirSync(directory, { recursive: true })
    execFileSync('tar', [
      '-xzf',
      tarball,
      '--strip-components=1',
      '-C',
      directory,
    ])
  }
  for (const alias of aliases)
    if (alias.replacement.startsWith(fixtureRoot))
      alias.replacement = alias.replacement.replace(fixtureRoot, bundleRoot)
} else await buildFixtures()
const bundles = await Promise.all(
  fixtureNames.map(
    async (name) =>
      (
        await import(
          `${resolve(bundleRoot, name, 'dist/theme.mjs')}?run=${Date.now()}`
        )
      ).themeBundle
  )
)
const themes = ['default', 'defense-green'].map((name) =>
  JSON.parse(
    readFileSync(
      resolve(root, `packages/theme-${name}/generated/theme.manifest.json`),
      'utf8'
    )
  )
)
const data = { themes, bundles }
const catalog = loadPackage(
  '@zxio/tokens/semantic-contract'
).themeSemanticCatalog

const expectations = Object.fromEntries(
  fixtureNames.map((name) => {
    const coverage = JSON.parse(
      readFileSync(resolve(fixtureRoot, name, 'coverage.json'), 'utf8')
    )
    return [
      name,
      coverage.variables.map((entry: any) => ({
        field: entry.assertion,
        variable: catalog.entries.find(
          (item: any) => item.path === entry.source.path
        ).css.publicVariable,
        fallback: entry.fallback,
      })),
    ]
  })
)

const { resolveThemeExtensionDeclarations } = loadPackage(
  '@zxio/tokens/extensions'
)
const { themeExtensionCssEncoder } = loadPackage('@zxio/theme-css-codec')

const matrix = []
for (const theme of themes)
  for (const variant of theme.variants) {
    const resolved = resolveThemeExtensionDeclarations({
      manifests: bundles.map((bundle) => bundle.manifest),
      axes: variant.selection,
      encoder: themeExtensionCssEncoder,
    })
    assert.equal(resolved.ok, true)
    matrix.push({
      themeId: theme.identity.themeId,
      variant: variant.variantKey,
    })
  }
await writeFile(
  resolve(output, 'axis-matrix.json'),
  JSON.stringify(
    { kind: 'composition-resolution-only', count: matrix.length, matrix },
    null,
    2
  )
)
function themeAsset(pkg: string, exported: string) {
  assert.ok(['@zxio/theme-default', '@zxio/theme-defense-green'].includes(pkg))
  assert.ok(exported.startsWith('./') && !exported.includes('..', 2))
  const directory = resolve(root, 'packages', pkg.slice(6))
  const manifest = JSON.parse(
    readFileSync(resolve(directory, 'package.json'), 'utf8')
  )
  let file = manifest.exports[exported]
  if (!file)
    for (const [key, value] of Object.entries(manifest.exports))
      if (key.endsWith('*') && exported.startsWith(key.slice(0, -1)))
        file = String(value).replace('*', exported.slice(key.length - 1))
  assert.equal(typeof file, 'string')
  return readFileSync(resolve(directory, file), 'utf8')
}
const config: any = {
  configFile: false,
  root,
  cacheDir: resolve(
    root,
    baseline
      ? 'node_modules/.consumer-vite-baseline'
      : 'node_modules/.consumer-vite'
  ),
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: true,
  },
  resolve: { alias: aliases, dedupe: ['vue', 'element-plus'] },
  optimizeDeps: {
    entries: [],
    noDiscovery: true,
    needsInterop: ['dayjs'],
    include: ['vue', 'element-plus', 'echarts', 'dayjs'],
  },
  ssr: { noExternal: [/^@zxio\//, 'element-plus'] },
  server: { host: '127.0.0.1', port: 0, hmr: false },
  plugins: [
    vue(),
    vueJsx(),
    {
      name: 'consumer-fixture',
      resolveId(id: string) {
        if (id === 'virtual:consumer-fixture') return '\0consumer-fixture'
      },
      load(id: string) {
        if (id === '\0consumer-fixture')
          return `export default ${JSON.stringify(data)}`
      },
      configureServer(server: any) {
        server.middlewares.use(
          async (request: any, response: any, next: any) => {
            const url = new URL(request.url, 'http://localhost')
            if (url.pathname === '/consumer-library-style') {
              const name = url.searchParams.get('name')!
              assert.ok((fixtureNames as readonly string[]).includes(name))
              response.setHeader('Content-Type', 'text/css')
              response.end(
                readFileSync(
                  resolve(bundleRoot, name, 'dist/style.css'),
                  'utf8'
                )
              )
              return
            }
            if (url.pathname === '/theme-asset') {
              try {
                response.setHeader('Content-Type', 'text/css')
                response.end(
                  themeAsset(
                    url.searchParams.get('package')!,
                    url.searchParams.get('export')!
                  )
                )
              } catch (error) {
                response.statusCode = 404
                response.end(String(error))
              }
              return
            }
            if (url.pathname !== '/consumer-ssr') return next()
            try {
              const renderer = await server.ssrLoadModule(
                '/scripts/theme-consumer-protocol/server-fixture.ts'
              )
              const initial = url.searchParams.get('initial')
                ? JSON.parse(url.searchParams.get('initial')!)
                : {}
              const rendered = await renderer.renderConsumerFrame(data, initial)
              const payload = {
                output: structuredClone(rendered.output),
                initial,
              }
              let html = rendered.html,
                styles = rendered.styles
              const tamper = url.searchParams.get('tamper')
              if (tamper === 'missing') delete payload.output.consumers
              if (tamper === 'sidecar')
                payload.output.consumers.appKey = 'foreign'
              if (tamper === 'attrs')
                html = html.replace(
                  'data-zx-consumer-state="ready"',
                  'data-zx-consumer-state="inactive"'
                )
              if (tamper === 'css')
                styles = styles.replace('</style>', '/*tampered*/</style>')
              if (tamper === 'version')
                payload.output.consumers.targets[0].actualVersion = '2.0.0'
              if (tamper === 'duplicate')
                payload.output.consumers.targets.push(
                  payload.output.consumers.targets[0]
                )
              if (tamper === 'scope')
                payload.output.consumers.targets[0].scopeId = 'foreign-scope'
              if (tamper === 'target-set')
                payload.output.consumers.targets.pop()
              if (tamper === 'request')
                payload.initial = { requestOverride: { mode: 'dark' } }
              if (tamper === 'destination-ownership')
                payload.output.consumers.destinations[0].ownership =
                  'transferred'
              if (
                payload.output.consumers &&
                [
                  'sidecar',
                  'version',
                  'duplicate',
                  'scope',
                  'target-set',
                  'destination-ownership',
                ].includes(tamper!)
              ) {
                const { integrity: _integrity, ...unsigned } =
                  payload.output.consumers
                payload.output.consumers = sealConsumerSnapshot(unsigned)
              }
              const core = rendered.output.stylesheets
                .map(
                  (style: any) =>
                    `<style data-zx-theme-artifact="${
                      style.artifactPath
                    }" data-zx-theme-artifact-hash="${
                      style.sha256
                    }">${themeAsset(
                      style.packageName,
                      style.exportPath
                    )}</style>`
                )
                .join('\n')
              response.setHeader('Content-Type', 'text/html')
              response.end(
                `<!doctype html><html><head><meta charset="UTF-8"><link rel="icon" href="data:,"><link rel="stylesheet" href="/consumer-library-style?name=acme-widget"><link rel="stylesheet" href="/consumer-library-style?name=example-panel">${core}${styles}</head><body><div id="app">${html}</div>${
                  rendered.portals
                }<script>window.__CONSUMER_SSR__=${JSON.stringify(
                  payload
                ).replaceAll(
                  '<',
                  '\\u003c'
                )}</script><script type="module" src="/scripts/theme-consumer-protocol/client.ts"></script></body></html>`
              )
            } catch (error) {
              response.statusCode = 500
              response.end(String(error))
            }
          }
        )
      },
    },
  ],
}
// Finish the declared dependency prebundle before measuring pages. A late Vite
// optimizer reload would invalidate the browser's execution context mid-assertion.
if (!process.argv.includes('--build-only'))
  await optimizeDeps(await resolveConfig(config, 'serve'), true, true)
const server = await createServer(config)
const receipts: any = {
  browser: 'chromium',
  scenarios: [],
  warnings: [],
  errors: [],
}
const sample = async (definitions: any) => {
  await Promise.all(
    document
      .getAnimations()
      .map((animation) => animation.finished.catch(() => undefined))
  )
  const fields = [
    'backgroundColor',
    'color',
    'borderTopColor',
    'outlineColor',
    'paddingTop',
    'borderTopLeftRadius',
    'transitionDuration',
  ]
  return [...document.querySelectorAll<HTMLElement>('[data-fixture]')].map(
    (element) => {
      const popup = document.querySelector<HTMLElement>(
        `[data-popup="${element.dataset.fixture}"]`
      )
      const style = getComputedStyle(element),
        overlay = popup ? getComputedStyle(popup) : null
      const name = element.classList.contains('acme-widget')
        ? 'acme-widget'
        : 'example-panel'
      const probe = document.createElement('span')
      for (const entry of definitions[name]) {
        const overridden =
          name === 'acme-widget' &&
          entry.field === 'paddingTop' &&
          (window as any).__CONSUMER__?.state.overrides
        ;(probe.style as any)[entry.field] =
          element.dataset.zxConsumerState === 'inactive'
            ? entry.fallback
            : overridden
            ? '19px'
            : `var(${entry.variable})`
      }
      element.append(probe)
      const expectedStyle = getComputedStyle(probe)
      const expected = Object.fromEntries(
        fields.map((field) => [field, (expectedStyle as any)[field]])
      )
      probe.remove()
      return {
        expected,
        label: element.dataset.fixture,
        state: element.dataset.zxConsumerState,
        theme: element.dataset.zxTheme,
        variant: element.dataset.zxVariant,
        root: Object.fromEntries(
          fields.map((field) => [field, (style as any)[field]])
        ),
        popup: overlay
          ? Object.fromEntries(
              fields.map((field) => [field, (overlay as any)[field]])
            )
          : null,
      }
    }
  )
}
try {
  if (process.argv.includes('--build-only')) {
    await build({
      ...config,
      build: {
        target: 'esnext',
        outDir: resolve(root, 'node_modules/.consumer-browser-dist'),
        emptyOutDir: true,
        rollupOptions: {
          input: resolve(root, 'scripts/theme-consumer-protocol/index.html'),
        },
      },
    })
    console.log('consumer browser build passed')
    process.exitCode = 0
  } else {
    await server.listen()
    const url = server.resolvedUrls!.local[0]!
    if (process.argv.includes('--serve')) {
      console.log(`${url}scripts/theme-consumer-protocol/index.html`)
      await new Promise<void>((done) => {
        process.once('SIGINT', done)
        process.once('SIGTERM', done)
      })
    } else {
      const { browser, identity } = await openGateBrowser()
      receipts.browserIdentity = identity
      try {
        const page = await browser.newPage({
          viewport: { width: 1400, height: 1000 },
        })
        await page.addInitScript(() => {
          ;(window as any).__name = (value: unknown) => value
        })
        // The server runs with `hmr: false`, yet Vite's client still tries its
        // socket. Browsers attached over CDP may block loopback WebSockets
        // (anti-fingerprinting), so that attempt alone is counted, not failed.
        receipts.ignoredHmrSocketMessages = 0
        const hmrSocketNoise =
          /^(?:WebSocket connection to 'ws:\/\/127\.0\.0\.1:\d+\/\?token=[^']*' failed|\[vite\] failed to connect to websocket)/
        page.on('console', (message) => {
          if (!['warning', 'error'].includes(message.type())) return
          if (identity.via === 'cdp' && hmrSocketNoise.test(message.text())) {
            receipts.ignoredHmrSocketMessages++
            return
          }
          receipts.warnings.push(message.text())
        })
        page.on('pageerror', (error) => receipts.errors.push(error.message))
        await page.goto(`${url}scripts/theme-consumer-protocol/index.html`)
        await page.waitForLoadState('networkidle')
        const ready = async () => {
          await page.waitForFunction(
            () => {
              const api = (window as any).__CONSUMER__
              if (api) {
                api.observedDiagnostics ??= []
                for (const node of document.querySelectorAll<HTMLElement>(
                  '[data-consumer-status="error"]'
                )) {
                  const diagnostic =
                    node.dataset.consumerDiagnostic ?? node.outerHTML
                  if (!api.observedDiagnostics.includes(diagnostic))
                    api.observedDiagnostics.push(diagnostic)
                }
              }
              return (
                api?.error ||
                (document.querySelectorAll<HTMLElement>('[data-fixture]')
                  .length > 0 &&
                  [
                    ...document.querySelectorAll<HTMLElement>('[data-fixture]'),
                  ].every((node) =>
                    ['ready', 'inactive'].includes(
                      node.dataset.consumerStatus ?? ''
                    )
                  ))
              )
            },
            undefined,
            { timeout: 30000 }
          )
          assert.equal(
            await page.evaluate(() => (window as any).__CONSUMER__.error),
            null
          )
          assert.deepEqual(
            await page
              .locator('[data-consumer-status="error"]')
              .evaluateAll((nodes) => nodes.map((node) => node.outerHTML)),
            []
          )
        }
        await ready()
        const initial = await page.evaluate(sample, expectations)
        const assertPair = (rows: any[]) => {
          assert.ok(rows.length >= 4)
          for (const row of rows) {
            assert.deepEqual(row.root, row.popup, row.label)
            assert.deepEqual(
              row.root,
              row.expected,
              `semantic expectation: ${row.label}`
            )
          }
        }
        assertPair(initial)
        receipts.scenarios.push({
          name: 'default-nested-dark-compact',
          computed: initial,
        })
        const scenarios: Array<[string, Record<string, unknown>]> = [
          ['second-theme', { themeId: 'defense-green' }],
          ['mode', { mode: 'dark' }],
          ['density', { density: 'comfortable' }],
          ['contrast', { contrast: 'high' }],
          ['motion', { motion: 'none' }],
          ['radius', { radius: 'sharp' }],
          ['seeds', { seeds: { brand: [0.42, 0.15, 0.56] } }],
          [
            'override',
            {
              overrides: {
                'acme-widget/gap': {
                  kind: 'literal',
                  value: { kind: 'value', value: 19, unit: 'px' },
                },
              },
            },
          ],
          ['inactive', { disabled: true, overrides: undefined }],
          ['reactivated', { disabled: false }],
          ['nested-inactive', { nestedDisabled: true }],
        ]
        for (const [name, patch] of scenarios) {
          console.log('scenario', name)
          const before = await page.evaluate(sample, expectations)
          const previous = await page
            .locator('.provider-root')
            .first()
            .evaluate((element) => element.dataset.zxComposition)
          await page.evaluate(
            (patch) => Object.assign((window as any).__CONSUMER__.state, patch),
            patch
          )
          if (name === 'nested-inactive')
            await page.waitForFunction(
              () =>
                document
                  .querySelector('[data-fixture="nested-a"]')
                  ?.getAttribute('data-zx-consumer-state') === 'inactive'
            )
          else
            await page.waitForFunction(
              (previous) =>
                document
                  .querySelector('.provider-root')
                  ?.getAttribute('data-zx-composition') !== previous,
              previous
            )
          await ready()
          const computed = await page.evaluate(sample, expectations)
          assertPair(computed)
          if (name === 'inactive')
            assert.equal(computed[0].root.backgroundColor, 'rgb(250, 250, 250)')
          if (name === 'override')
            assert.equal(computed[0].root.paddingTop, '19px')
          receipts.scenarios.push({ name, before, computed })
        }
        for (const library of ['acme-widget', 'example-panel']) {
          const button = page.locator(`.${library} button`).first()
          await button.hover()
          assert.equal(
            await button.evaluate(
              (node) => getComputedStyle(node).textDecorationLine
            ),
            'underline'
          )
          const states = await button.evaluate((node) => {
            const button = node as HTMLButtonElement
            const foreground = getComputedStyle(button).color
            const parentForeground = getComputedStyle(
              button.parentElement!
            ).color
            button.disabled = true
            const disabledOpacity = getComputedStyle(button).opacity
            button.disabled = false
            return { foreground, parentForeground, disabledOpacity }
          })
          assert.equal(states.foreground, states.parentForeground)
          assert.equal(states.disabledOpacity, '0.5')
          receipts.scenarios.push({
            name: `interaction-style-${library}`,
            ...states,
          })
        }
        const noOpBefore = await page.evaluate(sample, expectations)
        await page.evaluate(async () => {
          const api = (window as any).__CONSUMER__
          api.state.seeds = JSON.parse(JSON.stringify(api.state.seeds))
          await api.settle()
        })
        assert.deepEqual(await page.evaluate(sample, expectations), noOpBefore)
        receipts.scenarios.push({
          name: 'noop-keeps-computed-values',
          computed: noOpBefore,
        })
        // Error priority while inactive and isolation from another library use real public hooks.
        await page.evaluate(() => {
          ;(window as any).__CONSUMER__.state.disabled = true
        })
        await page.waitForFunction(
          () =>
            document
              .querySelector('[data-fixture="outer-a-0"]')
              ?.getAttribute('data-zx-consumer-state') === 'inactive'
        )
        const unaffected = (await page.evaluate(sample, expectations)).filter(
          (row: any) => row.label.includes('-b')
        )
        for (const failure of ['version', 'inline']) {
          await page.evaluate((failure) => {
            ;(window as any).__CONSUMER__.state.failureProbe = failure
          }, failure)
          await page.waitForFunction(
            () =>
              document
                .querySelector('[data-failure-probe]')
                ?.getAttribute('data-failure-probe') === 'error'
          )
          const diagnostic = await page
            .locator('[data-failure-probe]')
            .evaluate((node) => ({
              diagnostics: JSON.parse(node.dataset.probeDiagnostics!),
              owned: Object.hasOwn(node.dataset, 'zxConsumer'),
            }))
          assert.equal(diagnostic.owned, false)
          assert.equal(
            diagnostic.diagnostics[0].code,
            failure === 'version'
              ? 'TC_TARGET_VERSION_UNSUPPORTED'
              : 'TC_TARGET_OWNED'
          )
          assert.deepEqual(
            (await page.evaluate(sample, expectations)).filter((row: any) =>
              row.label.includes('-b')
            ),
            unaffected
          )
          receipts.scenarios.push({
            name: `inactive-reject-${failure}-preserves-other-library`,
            ...diagnostic,
          })
        }
        await page.evaluate(() => {
          ;(window as any).__CONSUMER__.state.failureProbe = ''
        })
        await page.waitForFunction(
          () => !document.querySelector('[data-failure-probe]')
        )
        const counts = () => ({
          targets: document.querySelectorAll('[data-zx-consumer]').length,
          coreStyles: document.querySelectorAll('[data-zx-theme-artifact]')
            .length,
          compositionStyles: document.querySelectorAll(
            '[data-zx-composition-style]'
          ).length,
          portals: (window as any).__CONSUMER__.host.runtime.snapshot().portals
            .hosts,
        })
        const resources: any = { instances: [], cycles: baseline ? 0 : 100 }
        for (const instances of [1, 10, 100]) {
          console.log('instances', instances)
          await page.evaluate(
            (instances) =>
              Object.assign((window as any).__CONSUMER__.state, { instances }),
            instances
          )
          await page.waitForFunction(
            (instances) =>
              document.querySelectorAll('[data-zx-consumer]').length ===
              (instances * 2 + 2) * 2,
            instances
          )
          await ready()
          resources.instances.push({
            instances,
            counts: await page.evaluate(counts),
          })
        }
        assert.equal(
          resources.instances[0].counts.compositionStyles,
          resources.instances[2].counts.compositionStyles,
          'composition CSS shared independent of instances'
        )
        assert.equal(
          resources.instances[0].counts.coreStyles,
          resources.instances[2].counts.coreStyles,
          'core CSS shared independent of instances'
        )
        await page.evaluate(() =>
          Object.assign((window as any).__CONSUMER__.state, { instances: 1 })
        )
        for (let cycle = 0; cycle < (baseline ? 0 : 100); cycle++) {
          if (cycle % 10 === 0) console.log('resource cycle', cycle)
          await page.evaluate(() => {
            ;(window as any).__CONSUMER__.state.show = false
          })
          await page.waitForFunction(
            () => !document.querySelector('[data-zx-consumer]')
          )
          await page.evaluate(
            (cycle) =>
              Object.assign((window as any).__CONSUMER__.state, {
                show: true,
                mode: cycle % 2 ? 'light' : 'dark',
              }),
            cycle
          )
          await page.waitForFunction(
            (mode) =>
              document
                .querySelector<HTMLElement>('[data-fixture="outer-a-0"]')
                ?.closest<HTMLElement>('[data-zx-variant]')
                ?.dataset.zxVariant?.startsWith(`mode-${mode}__`),
            cycle % 2 ? 'light' : 'dark'
          )
          await ready()
          await page.waitForFunction(
            () => document.querySelectorAll('[data-zx-consumer]').length === 8
          )
        }
        resources.afterCycles = await page.evaluate(counts)
        resources.observedDiagnostics = await page.evaluate(
          () => (window as any).__CONSUMER__.observedDiagnostics ?? []
        )
        for (const observed of resources.observedDiagnostics) {
          assert.ok(
            JSON.parse(observed).every(
              (item: any) => item.code === 'TR_TRANSACTION_STALE'
            ),
            observed
          )
        }
        assert.ok(resources.afterCycles.portals.length <= 2)
        await page.screenshot({
          path: resolve(
            output,
            baseline ? 'baseline-browser.png' : 'browser.png'
          ),
          fullPage: true,
        })
        console.log('dispose resources')
        await page.evaluate(() => (window as any).__CONSUMER__.unmount())
        await page.waitForFunction(
          () => !document.querySelector('[data-zx-consumer]')
        )
        resources.disposed = await page.evaluate(counts)
        assert.deepEqual(resources.disposed, {
          targets: 0,
          coreStyles: 0,
          compositionStyles: 0,
          portals: [],
        })
        resources.status = 'pass'
        await writeFile(
          resolve(
            output,
            baseline ? 'baseline-resources.json' : 'resources.json'
          ),
          JSON.stringify(resources, null, 2)
        )
        for (const initial of [
          {},
          { themeId: 'defense-green', seeds: { brand: [0.42, 0.15, 0.56] } },
          { nestedDisabled: true },
        ]) {
          const context = await browser.newContext({ javaScriptEnabled: false })
          const first = await context.newPage()
          const response = await first.goto(
            `${url}consumer-ssr?initial=${encodeURIComponent(
              JSON.stringify(initial)
            )}`
          )
          assert.equal(response?.status(), 200, await response?.text())
          const computed = await first.evaluate(sample, expectations)
          assertPair(computed)
          receipts.scenarios.push({
            name: 'ssr-no-javascript',
            initial,
            computed,
          })
          await first.screenshot({
            path: resolve(
              output,
              `${baseline ? 'baseline-' : ''}ssr-no-js-${
                'themeId' in initial
                  ? 'seeded'
                  : 'nestedDisabled' in initial
                  ? 'inactive'
                  : 'default'
              }.png`
            ),
            fullPage: true,
          })
          await context.close()
        }
        for (const customPortal of [false, true]) {
          await page.goto(
            `${url}consumer-ssr?initial=${encodeURIComponent(
              JSON.stringify({ customPortal })
            )}`
          )
          await page.waitForFunction(
            () =>
              (window as any).__CONSUMER__?.complete ||
              (window as any).__CONSUMER__?.error
          )
          assert.equal(
            await page.evaluate(() => (window as any).__CONSUMER__.error),
            null
          )
          assert.deepEqual(
            await page.evaluate(() => (window as any).__CONSUMER_REUSED__),
            { nodes: true, styles: true }
          )
          assertPair(await page.evaluate(sample, expectations))
          receipts.scenarios.push({
            name: 'hydration-reuses-nodes-and-styles',
            customPortal,
            computed: await page.evaluate(sample, expectations),
          })
          await page.evaluate(() => (window as any).__CONSUMER__.unmount())
          assert.equal(await page.locator('[data-zx-consumer]').count(), 0)
          assert.equal(
            await page.locator('[data-zx-consumer-portal]').count(),
            0
          )
          assert.equal(
            await page.locator('[data-zx-consumer-destination]').count(),
            customPortal ? 1 : 0
          )
        }
        for (const kind of [
          'missing',
          'sidecar',
          'attrs',
          'css',
          'version',
          'duplicate',
          'scope',
          'target-set',
          'request',
          'destination-ownership',
        ]) {
          let resume!: () => void
          let intercepted!: () => void
          const gate = new Promise<void>((done) => {
            resume = done
          })
          const seen = new Promise<void>((done) => {
            intercepted = done
          })
          const routePattern = '**/scripts/theme-consumer-protocol/client.ts'
          await page.route(routePattern, async (route) => {
            intercepted()
            await gate
            await route.continue()
          })
          const initial =
            kind === 'destination-ownership'
              ? `&initial=${encodeURIComponent(
                  JSON.stringify({ customPortal: true })
                )}`
              : ''
          const navigation = page.goto(
            `${url}consumer-ssr?tamper=${kind}${initial}`
          )
          await seen
          await page.waitForFunction(
            () =>
              document.querySelectorAll('[data-zx-consumer]').length === 8 &&
              [
                ...document.querySelectorAll<HTMLLinkElement>(
                  'link[rel="stylesheet"]'
                ),
              ].every((link) => link.sheet)
          )
          const before = await page.evaluate(captureSsrFrame)
          resume()
          await navigation
          await page.unroute(routePattern)
          await page.waitForFunction(() => (window as any).__CONSUMER__?.error)
          const diagnostics = await page.evaluate(
            () => (window as any).__CONSUMER__.error
          )
          const expected =
            kind === 'request'
              ? { code: 'TR_COMPOSITION_HYDRATION_INVALID', phase: 'hydration' }
              : { code: 'CONSUMER_HOST_BIND_FAILED', phase: 'owner' }
          assert.equal(diagnostics[0].code, expected.code)
          assert.equal(diagnostics[0].phase, expected.phase)
          if (kind !== 'request')
            assert.equal(
              diagnostics[0].details.runtimeCode,
              'TR_COMPOSITION_HYDRATION_INVALID'
            )
          const retained = await page.evaluate(inspectRetainedFrame)
          for (const field of [
            'nodes',
            'attributes',
            'computed',
            'styles',
            'noReady',
            'noOwnership',
          ] as const)
            assert.equal(retained[field], true, `${kind}: ${field}`)
          await page.evaluate(async () => {
            await (window as any).__CONSUMER__.host?.dispose()
          })
          const afterDispose = await page.evaluate(inspectRetainedFrame)
          for (const field of [
            'nodes',
            'attributes',
            'computed',
            'styles',
            'noReady',
            'noOwnership',
          ] as const)
            assert.equal(
              afterDispose[field],
              true,
              `${kind} after dispose: ${field}`
            )
          receipts.scenarios.push({
            name: `reject-${kind}`,
            diagnostics,
            before,
            retained,
            afterDispose,
          })
        }
        assert.deepEqual(receipts.warnings, [])
        assert.deepEqual(receipts.errors, [])
        receipts.status = 'pass'
      } finally {
        await browser.close()
      }
    }
  }
} catch (error) {
  receipts.status = 'fail'
  receipts.failure = String(error)
  throw error
} finally {
  await server.close()
  if (
    !process.argv.includes('--build-only') &&
    !process.argv.includes('--serve')
  ) {
    await writeFile(
      resolve(
        output,
        baseline ? 'baseline-browser-receipt.json' : 'browser-receipt.json'
      ),
      JSON.stringify(receipts, null, 2)
    )
    await writeFile(
      resolve(
        output,
        baseline ? 'baseline-ssr-receipt.json' : 'ssr-receipt.json'
      ),
      JSON.stringify(
        {
          status: receipts.status,
          scenarios: receipts.scenarios.filter((scenario: any) =>
            /^(ssr|hydration|reject-)/.test(scenario.name)
          ),
          warnings: receipts.warnings,
          errors: receipts.errors,
        },
        null,
        2
      )
    )
  }
}
