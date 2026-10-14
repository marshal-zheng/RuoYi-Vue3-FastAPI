import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import {
  cpSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  writeFileSync,
} from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'node:http'
import { build } from 'vite'
import { buildFixtures, fixtureNames, fixtureRoot } from './build-fixtures.mts'
import { openGateBrowser } from './gate-browser.mts'

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
export const packedRoot = resolve(root, 'node_modules/.consumer-packed')
const tarDir = resolve(packedRoot, 'tarballs')
const consumer = resolve(packedRoot, 'consumer')
const output = resolve(
  root,
  'docs/specs/THEME-theme-consumer-protocol/evidence'
)
export const hash = (path: string) =>
  `sha256:${createHash('sha256').update(readFileSync(path)).digest('hex')}`
export function run(cmd: string, args: string[], cwd = root) {
  return execFileSync(cmd, args, {
    cwd,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
    env: { ...process.env, NODE_PATH: '' },
  })
}
export async function checkPacked() {
  mkdirSync(tarDir, { recursive: true })
  mkdirSync(consumer, { recursive: true })
  await buildFixtures()
  run('pnpm', ['-C', 'packages/theme-consumer', 'build'])
  const artifacts = [
    'packages/theme-consumer',
    ...fixtureNames.map((name) => resolve(fixtureRoot, name)),
  ].map((directory) => {
    const manifest = JSON.parse(
      readFileSync(resolve(root, directory, 'package.json'), 'utf8')
    )
    run(
      'pnpm',
      ['pack', '--pack-destination', tarDir],
      resolve(root, directory)
    )
    const tarball = resolve(
      tarDir,
      `${manifest.name.replace('@', '').replace('/', '-')}-${
        manifest.version
      }.tgz`
    )
    return {
      packageName: manifest.name,
      version: manifest.version,
      tarball,
      sha256: hash(tarball),
    }
  })
  const dependencies = Object.fromEntries(
    artifacts.map((artifact) => [
      artifact.packageName,
      `file:${artifact.tarball}`,
    ])
  )
  const rootRequire = createRequire(resolve(root, 'package.json'))
  dependencies.vue = rootRequire('vue/package.json').version
  dependencies.typescript = rootRequire('typescript/package.json').version
  writeFileSync(
    resolve(consumer, 'package.json'),
    JSON.stringify(
      {
        name: 'isolated-consumer',
        private: true,
        type: 'module',
        dependencies,
      },
      null,
      2
    )
  )
  writeFileSync(
    resolve(consumer, '.npmrc'),
    'registry=https://registry.npmjs.org\nauto-install-peers=false\nlink-workspace-packages=false\n'
  )
  run(
    'pnpm',
    [
      'install',
      '--force',
      '--ignore-workspace',
      '--offline',
      '--ignore-scripts',
    ],
    consumer
  )
  const require = createRequire(resolve(consumer, 'package.json'))
  for (const artifact of artifacts)
    assert.ok(
      realpathSync(require.resolve(artifact.packageName)).startsWith(consumer),
      'package must resolve inside isolated installation'
    )
  writeFileSync(
    resolve(consumer, 'esm.mjs'),
    `import assert from 'node:assert/strict'; import * as protocol from '@zxio/theme-consumer'; import { increment } from '@acme/widget'; import { themeBundle } from '@example/panel/theme'; assert.equal(increment(1),2); assert.equal(protocol.themeConsumerScopeKey,Symbol.for('zx.theme-consumer.scope/1')); assert.ok(themeBundle.manifest); try { await import('@zxio/theme-consumer/src/protocol'); throw Error('deep import accepted') } catch(e) { assert.equal(e.code,'ERR_PACKAGE_PATH_NOT_EXPORTED') }`
  )
  writeFileSync(
    resolve(consumer, 'cjs.cjs'),
    `const assert=require('node:assert/strict'); assert.equal(require('@example/panel').increment(2),3); assert.equal(typeof require('@zxio/theme-consumer/vue').useThemeCssAdapter,'function'); assert.ok(require('@acme/widget/theme').themeBundle.manifest);`
  )
  run('node', ['esm.mjs'], consumer)
  run('node', ['cjs.cjs'], consumer)
  writeFileSync(
    resolve(consumer, 'types.ts'),
    `import { useThemeCssAdapter, useThemePortalBinding } from '@zxio/theme-consumer/vue'; import { ref } from 'vue'; import type { ThemeConsumerScopePort } from '@zxio/theme-consumer'; import { Widget } from '@acme/widget/vue'; const portal=useThemePortalBinding({active:ref(true)}); const css=useThemeCssAdapter(ref<HTMLElement|null>(null),{id:'acme-widget-css',actualVersion:'1.0.0'},{portal}); void [css,Widget]; declare const port: ThemeConsumerScopePort<HTMLElement,HTMLElement>; port.snapshot();`
  )
  for (const [name, module, moduleResolution] of [
    ['bundler', 'ESNext', 'Bundler'],
    ['nodenext', 'NodeNext', 'NodeNext'],
    ['node16', 'Node16', 'Node16'],
  ]) {
    writeFileSync(
      resolve(consumer, `tsconfig.${name}.json`),
      JSON.stringify({
        compilerOptions: {
          target: 'ES2022',
          module,
          moduleResolution,
          strict: true,
          skipLibCheck: false,
          noEmit: true,
          types: [],
          lib: ['ES2022', 'DOM'],
        },
        files: ['types.ts'],
      })
    )
    run(
      'node',
      [require.resolve('typescript/bin/tsc'), '-p', `tsconfig.${name}.json`],
      consumer
    )
  }
  const coreOnly = resolve(packedRoot, 'core-only')
  mkdirSync(coreOnly, { recursive: true })
  writeFileSync(
    resolve(coreOnly, '.npmrc'),
    'registry=https://registry.npmjs.org\nauto-install-peers=false\nlink-workspace-packages=false\n'
  )
  writeFileSync(
    resolve(coreOnly, 'package.json'),
    JSON.stringify({
      private: true,
      type: 'module',
      dependencies: {
        ...Object.fromEntries(
          artifacts
            .slice(1)
            .map((artifact) => [
              artifact.packageName,
              `file:${artifact.tarball}`,
            ])
        ),
        typescript: dependencies.typescript,
      },
    })
  )
  run(
    'pnpm',
    [
      'install',
      '--force',
      '--ignore-workspace',
      '--offline',
      '--ignore-scripts',
    ],
    coreOnly
  )
  const coreGraph = JSON.parse(
    run('pnpm', ['list', '--depth', 'Infinity', '--json'], coreOnly)
  )
  assert.ok(
    !JSON.stringify(coreGraph).includes('"vue":') &&
      !JSON.stringify(coreGraph).includes('"@zxio/'),
    'pure core installs no Vue or ZX packages'
  )
  writeFileSync(
    resolve(coreOnly, 'check.mjs'),
    "import assert from 'node:assert/strict'; import {increment} from '@acme/widget'; import {createRequire} from 'node:module'; const require=createRequire(import.meta.url); assert.equal(increment(1),2); assert.equal(require('@example/panel').increment(4),5)"
  )
  writeFileSync(
    resolve(coreOnly, 'types.ts'),
    "import {increment} from '@acme/widget'; const value:number=increment(2)"
  )
  writeFileSync(
    resolve(coreOnly, 'types.cts'),
    "import {increment} from '@example/panel'; const value:number=increment(2)"
  )
  run('node', ['check.mjs'], coreOnly)
  run(
    'pnpm',
    [
      'exec',
      'tsc',
      '--noEmit',
      '--module',
      'NodeNext',
      '--moduleResolution',
      'NodeNext',
      '--target',
      'ES2022',
      '--skipLibCheck',
      'false',
      'types.ts',
      'types.cts',
    ],
    coreOnly
  )
  writeFileSync(
    resolve(consumer, 'protocol-types.cts'),
    "import {useThemeCssAdapter} from '@zxio/theme-consumer/vue'; import {Widget} from '@acme/widget/vue'; void [useThemeCssAdapter,Widget]"
  )
  run(
    'node',
    [
      require.resolve('typescript/bin/tsc'),
      '--noEmit',
      '--module',
      'NodeNext',
      '--target',
      'ES2022',
      '--skipLibCheck',
      'false',
      'protocol-types.cts',
    ],
    consumer
  )
  // Install a second physical copy. Public symbols and structural leases must bridge ESM/CJS copies.
  const copy = resolve(consumer, 'node_modules/consumer-copy-b')
  mkdirSync(copy, { recursive: true })
  run('tar', [
    '-xzf',
    artifacts[0]!.tarball,
    '--strip-components=1',
    '-C',
    copy,
  ])
  cpSync(
    resolve(root, 'scripts/theme-consumer-protocol/packed-browser.ts'),
    resolve(consumer, 'entry.ts')
  )
  const modules: string[] = []
  await build({
    root: consumer,
    configFile: false,
    define: {
      __VUE_OPTIONS_API__: true,
      __VUE_PROD_DEVTOOLS__: false,
      'process.env.NODE_ENV': JSON.stringify('production'),
    },
    build: {
      outDir: 'dist',
      lib: {
        entry: resolve(consumer, 'entry.ts'),
        formats: ['iife'],
        name: 'Proof',
        fileName: () => 'proof.js',
      },
      rollupOptions: {
        plugins: [
          {
            name: 'audit-modules',
            moduleParsed(info) {
              modules.push(info.id)
            },
          },
        ],
      },
    },
  })
  for (const id of modules)
    if (id.includes('/@zxio/')) assert.match(id, /\/theme-consumer\//, id)
  assert.ok(
    modules.every(
      (id) => !/packages\/(zxui|tokens|theme-compiler|components)\//.test(id)
    )
  )
  const server = createServer((_, response) => {
    response.setHeader(
      'Content-Type',
      _.url === '/proof.js' ? 'text/javascript' : 'text/html'
    )
    response.end(
      _.url === '/proof.js'
        ? readFileSync(resolve(consumer, 'dist/proof.js'))
        : '<!doctype html><div id="app"></div><script src="/proof.js"></script>'
    )
  })
  await new Promise<void>((done) => server.listen(0, '127.0.0.1', done))
  const { browser, identity: browserIdentity } = await openGateBrowser()
  let crossCopy: unknown
  try {
    const page = await browser.newPage()
    const errors: string[] = []
    page.on('pageerror', (error) => errors.push(error.stack ?? error.message))
    await page.goto(`http://127.0.0.1:${(server.address() as any).port}`)
    await page
      .waitForFunction(() => (window as any).__PACKED__)
      .catch((error) => {
        throw new Error(JSON.stringify({ errors, timeout: String(error) }))
      })
    crossCopy = await page.evaluate(() => (window as any).__PACKED__)
    if (errors.length) console.error(JSON.stringify({ crossCopy, errors }))
    assert.deepEqual(errors, [])
    assert.equal((crossCopy as any).status, 'pass')
  } finally {
    await browser.close()
    await new Promise<void>((done) => server.close(() => done()))
  }
  const receipt = {
    status: 'pass',
    node: process.version,
    pnpm: run('pnpm', ['--version']).trim(),
    artifacts,
    installation: dependencies,
    pureCore: { status: 'pass', graph: coreGraph, types: ['ESM', 'CJS'] },
    esm: 'pass',
    cjs: 'pass',
    types: ['Bundler', 'NodeNext', 'Node16'],
    crossCopy,
    browserIdentity,
    modules,
  }
  writeFileSync(
    resolve(output, 'packed-receipt.json'),
    JSON.stringify(receipt, null, 2)
  )
  console.log(
    'Packed ESM/CJS/types, module graph, and cross-copy portal/CSS tests passed.'
  )
  return receipt
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await checkPacked()
