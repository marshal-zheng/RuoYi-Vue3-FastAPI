import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  realpathSync,
  writeFileSync,
} from 'node:fs'
import { dirname, resolve } from 'node:path'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import { createServer } from 'node:http'
import { build } from 'vite'
import { openGateBrowser } from './gate-browser.mts'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const directory = resolve(root, 'node_modules/.consumer-hosted-packed')
const tarballs = resolve(directory, 'tarballs'),
  consumer = resolve(directory, 'consumer')
mkdirSync(tarballs, { recursive: true })
mkdirSync(consumer, { recursive: true })
const run = (command: string, args: string[], cwd = root) =>
  execFileSync(command, args, {
    cwd,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
    env: { ...process.env, NODE_PATH: '' },
  })
const artifacts: any[] = []
for (const name of [
  'constants',
  'types',
  'utils',
  'shared',
  'hooks',
  'mcp-core',
  'keybindings',
  'tokens',
  'theme-css-codec',
  'theme-consumer',
  'theme-default',
  'theme-defense-green',
  'zxui',
]) {
  console.log('pack dependency', name)
  const source = resolve(root, 'packages', name)
  // Theme artifacts are already generated and content checked; root build ran in the aggregate gate.
  if (
    !process.argv.includes('--reuse-builds') &&
    !['zxui', 'theme-default', 'theme-defense-green'].includes(name)
  )
    run('pnpm', ['-C', source, 'build'])
  const stage =
    name === 'zxui'
      ? resolve(root, 'dist/@zxio/zxui')
      : ['theme-default', 'theme-defense-green'].includes(name)
      ? source
      : existsSync(resolve(source, 'dist/package.json'))
      ? resolve(source, 'dist')
      : source
  const manifest = JSON.parse(
    readFileSync(resolve(stage, 'package.json'), 'utf8')
  )
  run('pnpm', ['pack', '--pack-destination', tarballs], stage)
  const tarball = resolve(
    tarballs,
    `${manifest.name.replace('@', '').replace('/', '-')}-${
      manifest.version
    }.tgz`
  )
  artifacts.push({
    packageName: manifest.name,
    version: manifest.version,
    tarball,
    sha256: `sha256:${createHash('sha256')
      .update(readFileSync(tarball))
      .digest('hex')}`,
  })
}
const current = JSON.parse(
  readFileSync(
    resolve(
      root,
      'docs/specs/THEME-theme-consumer-protocol/evidence/packed-receipt.json'
    ),
    'utf8'
  )
)
for (const artifact of current.artifacts.filter(
  (item: any) => !item.packageName.startsWith('@zxio/')
))
  artifacts.push(artifact)
const requireRoot = createRequire(resolve(root, 'package.json'))
const overrides = Object.fromEntries(
  artifacts.map((artifact) => [
    artifact.packageName,
    `file:${artifact.tarball}`,
  ])
)
const dependencies = {
  ...overrides,
  vue: requireRoot('vue/package.json').version,
  'element-plus': requireRoot('element-plus/package.json').version,
  typescript: requireRoot('typescript/package.json').version,
}
writeFileSync(
  resolve(consumer, 'package.json'),
  JSON.stringify(
    { private: true, type: 'module', dependencies, pnpm: { overrides } },
    null,
    2
  )
)
writeFileSync(
  resolve(consumer, '.npmrc'),
  'registry=https://registry.npmjs.org\nauto-install-peers=false\nlink-workspace-packages=false\n'
)
run('pnpm', ['install', '--ignore-workspace', '--ignore-scripts'], consumer)
const require = createRequire(resolve(consumer, 'package.json'))
for (const artifact of artifacts)
  assert.ok(
    realpathSync(
      require.resolve(
        artifact.packageName === '@zxio/tokens'
          ? '@zxio/tokens/kernel'
          : artifact.packageName === '@zxio/theme-default' ||
            artifact.packageName === '@zxio/theme-defense-green'
          ? `${artifact.packageName}/manifest.json`
          : artifact.packageName
      )
    ).startsWith(consumer)
  )
cpSync(
  resolve(root, 'scripts/theme-consumer-protocol/app.ts'),
  resolve(consumer, 'app.ts')
)
cpSync(
  resolve(root, 'scripts/theme-consumer-protocol/server-fixture.ts'),
  resolve(consumer, 'server-fixture.ts')
)
cpSync(
  resolve(root, 'scripts/theme-consumer-protocol/client.ts'),
  resolve(consumer, 'client.ts')
)
const data = {
  themes: ['@zxio/theme-default', '@zxio/theme-defense-green'].map((name) =>
    require(`${name}/manifest.json`)
  ),
  bundles: ['@acme/widget', '@example/panel'].map(
    (name) => require(`${name}/theme`).themeBundle
  ),
}
const modules: string[] = []
// No resolve.alias and no workspace fallback. All hosted browser modules must come from installed tarballs.
await build({
  root: consumer,
  configFile: false,
  define: { __VUE_OPTIONS_API__: true, __VUE_PROD_DEVTOOLS__: false },
  plugins: [
    {
      name: 'data',
      resolveId(id) {
        if (id === 'virtual:consumer-fixture') return '\0data'
      },
      load(id) {
        if (id === '\0data') return `export default ${JSON.stringify(data)}`
      },
    },
  ],
  build: {
    target: 'esnext',
    outDir: 'dist',
    rollupOptions: {
      input: resolve(consumer, 'client.ts'),
      output: { entryFileNames: 'client.js' },
      plugins: [
        {
          name: 'installed-graph',
          moduleParsed(info) {
            modules.push(info.id)
            if (info.id.includes('/packages/') && !info.id.startsWith(consumer))
              throw new Error(`source fallback: ${info.id}`)
          },
        },
      ],
    },
  },
})
// Execute the public server leaf from this exact installation in Node, with the same old/current UI components.
writeFileSync(
  resolve(consumer, 'ssr.mjs'),
  `import {createSSRApp,h} from 'vue'; import {renderToString} from 'vue/server-renderer'; import {ZxThemeProvider} from '@zxio/zxui/theme-provider'; import {createDefaultServerThemeHost,renderThemeConsumerPortals} from '@zxio/zxui/theme-host/server'; import {Widget} from '@acme/widget/vue'; import {themeBundle} from '@acme/widget/theme'; import {createRequire} from 'node:module'; const require=createRequire(import.meta.url); const host=createDefaultServerThemeHost({appKey:'packed',themes:[{manifest:require('@zxio/theme-default/manifest.json')}],defaultThemeId:'default',systemMode:'light',extensions:[themeBundle]}); if(!host.ok)throw Error(JSON.stringify(host.diagnostics)); const app=createSSRApp({render:()=>h(ZxThemeProvider,{},()=>h(Widget,{label:'packed'}))}); host.value.bind(app); const context={}; const html=await renderToString(app,context); const out=host.value.collect(); if(!out.ok)throw Error(JSON.stringify(out.diagnostics)); if(out.value.consumers.targets.length!==2)throw Error('missing targets'); const portals=renderThemeConsumerPortals(out.value,context.teleports); if(!portals.body.includes('Popup packed'))throw Error('missing portal'); host.value.dispose(); console.log(JSON.stringify({targets:out.value.consumers.targets.length,html:html.length,portal:portals.body.length}));`
)
const ssr = JSON.parse(run('node', ['ssr.mjs'], consumer).trim())
const server = createServer((request, response) => {
  const url = new URL(request.url!, 'http://localhost')
  try {
    if (url.pathname === '/theme-asset') {
      const pkg = url.searchParams.get('package')!,
        leaf = url.searchParams.get('export')!
      assert.ok(
        ['@zxio/theme-default', '@zxio/theme-defense-green'].includes(pkg)
      )
      response.setHeader('Content-Type', 'text/css')
      response.end(readFileSync(require.resolve(`${pkg}/${leaf.slice(2)}`)))
    } else if (url.pathname === '/') {
      const css = readdirSync(resolve(consumer, 'dist/assets')).filter((file) =>
        file.endsWith('.css')
      )
      response.setHeader('Content-Type', 'text/html')
      response.end(
        `<!doctype html><html><head><link rel="icon" href="data:,">${css
          .map((file) => `<link rel="stylesheet" href="/assets/${file}">`)
          .join(
            ''
          )}</head><body><div id="app"></div><script type="module" src="/client.js"></script></body></html>`
      )
    } else {
      assert.ok(!url.pathname.includes('..'))
      response.setHeader(
        'Content-Type',
        url.pathname.endsWith('.css') ? 'text/css' : 'text/javascript'
      )
      response.end(readFileSync(resolve(consumer, 'dist', `.${url.pathname}`)))
    }
  } catch (error) {
    response.statusCode = 500
    response.end(String(error))
  }
})
await new Promise<void>((done) => server.listen(0, '127.0.0.1', done))
const { browser, identity: browserIdentity } = await openGateBrowser()
let browserProof: unknown
try {
  const page = await browser.newPage(),
    warnings: string[] = []
  page.on('pageerror', (error) => warnings.push(error.message))
  page.on('console', (event) => {
    if (['error', 'warning'].includes(event.type())) warnings.push(event.text())
  })
  await page.goto(`http://127.0.0.1:${(server.address() as any).port}/`)
  await page.waitForFunction(
    () => document.querySelectorAll('[data-zx-consumer]').length === 8
  )
  await page.evaluate(async () => {
    await Promise.all(
      document
        .getAnimations()
        .map((animation) => animation.finished.catch(() => undefined))
    )
  })
  const styles = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('[data-fixture]')].map(
      (root) => ({
        label: root.dataset.fixture,
        root: getComputedStyle(root).backgroundColor,
        popup: getComputedStyle(
          document.querySelector(`[data-popup="${root.dataset.fixture}"]`)!
        ).backgroundColor,
      })
    )
  )
  for (const item of styles) assert.equal(item.root, item.popup)
  await page.evaluate(() => (window as any).__CONSUMER__.unmount())
  assert.equal(await page.locator('[data-zx-consumer]').count(), 0)
  assert.deepEqual(warnings, [])
  browserProof = { status: 'pass', styles, warnings, disposedTargets: 0 }
} finally {
  await browser.close()
  await new Promise<void>((done) => server.close(() => done()))
}
writeFileSync(
  resolve(
    root,
    'docs/specs/THEME-theme-consumer-protocol/evidence/hosted-packed.json'
  ),
  JSON.stringify(
    {
      status: 'pass',
      artifacts,
      ssr,
      browserBuild: 'installed-only',
      browser: browserProof,
      browserIdentity,
      modules,
    },
    null,
    2
  )
)
console.log('Installed hosted public leaves and SSR passed.')
