import gulp from 'gulp'
import { rollup } from 'rollup'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import VueMacros from 'unplugin-vue-macros/rollup'
import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'
import json from '@rollup/plugin-json'
import esbuild from 'rollup-plugin-esbuild'
import glob from 'fast-glob'
import {
  epRoot,
  excludeFiles,
  excludeStandalonePackages,
  normalizePath,
  pkgRoot,
} from '@zxio/build-utils'
import {
  generateExternal,
  getExternalPackages,
  isExternalPackage,
  toExternalId,
  withTaskName,
  writeBundles,
} from '../utils'
import { ElementPlusAlias } from '../plugins/element-plus-alias'
import { buildConfigEntries, target } from '../build-info'
import { createDeterministicModuleInputs } from '../utils/module-inputs'

import type { TaskFunction } from 'gulp'
import type { OutputOptions, Plugin } from 'rollup'

type GulpTaskComposer = (...tasks: TaskFunction[]) => TaskFunction

const { series } = gulp as unknown as {
  series: GulpTaskComposer
}

const publicStyleFacadePattern = /(?:^|[\\/])(?:style|style-css)\.[cm]?[jt]s$/

const elementPlusCjsSubpaths: Readonly<Record<string, string>> = Object.freeze({
  'element-plus/es/components/message/index':
    'element-plus/lib/components/message/index',
  'element-plus/es/components/message-box/index':
    'element-plus/lib/components/message-box/index',
  'element-plus/es/components/notification/index':
    'element-plus/lib/components/notification/index',
})

// 创建一个插件，处理外部化的包
function externalPackagesPlugin(): Plugin {
  const externalPackages = getExternalPackages()

  return {
    name: 'external-packages',
    resolveId(id) {
      // 1. 处理 @zxio/xxx 形式的导入
      if (
        externalPackages.some((pkg) => id === pkg || id.startsWith(`${pkg}/`))
      ) {
        return { id, external: true }
      }

      // 2. 处理已经被解析成绝对路径的情况
      const externalId = toExternalId(id)
      if (externalId) {
        return { id: externalId, external: true }
      }

      return null
    },
    // 备用：如果 resolveId 没有拦截到，在 load 阶段处理
    load(id) {
      if (isExternalPackage(id)) {
        const externalId = toExternalId(id)
        if (externalId) {
          return `export * from '${externalId}';`
        }
      }
      return null
    },
  }
}

async function getPlugins(): Promise<Plugin[]> {
  const vueMacros = await VueMacros({
    setupComponent: false,
    setupSFC: false,
    // Vue 3.5 resolves imported props natively, without betterDefine's async cache.
    betterDefine: false,
    plugins: {
      vue: vue({
        isProduction: true,
        template: {
          compilerOptions: {
            hoistStatic: false,
            cacheHandlers: false,
          },
        },
      }),
      vueJsx: vueJsx(),
    },
  })

  const vueMacrosPlugins = Array.isArray(vueMacros) ? vueMacros : [vueMacros]

  return [
    // 首先处理外部化的包 - 必须在所有其他插件之前
    externalPackagesPlugin(),
    ElementPlusAlias(),
    ...vueMacrosPlugins,
    nodeResolve({
      extensions: ['.mjs', '.js', '.json', '.ts'],
    }),
    commonjs(),
    json(),
    esbuild({
      sourceMap: false,
      target,
      loaders: {
        '.vue': 'ts',
      },
      define: {
        'process.env.NODE_ENV': '"production"',
      },
    }),
  ]
}

async function buildModulesComponents() {
  const files = excludeStandalonePackages(
    excludeFiles(
      await glob(['**/*.{js,ts,vue}', '!**/style/(index|css).{js,ts,vue}'], {
        cwd: pkgRoot,
        absolute: true,
        onlyFiles: true,
      })
    )
  )
  const moduleInputs = createDeterministicModuleInputs(files, pkgRoot, epRoot)
  const bundle = await rollup({
    input: [...moduleInputs.input],
    plugins: await getPlugins(),
    external: await generateExternal({ full: false }),
    treeshake: {
      moduleSideEffects: (id) => publicStyleFacadePattern.test(id),
    },
  })

  await writeBundles(
    bundle,
    buildConfigEntries.map(([module, config]): OutputOptions => {
      return {
        format: config.format,
        dir: config.output.path,
        exports: module === 'cjs' ? 'named' : undefined,
        paths: module === 'cjs' ? elementPlusCjsSubpaths : undefined,
        preserveModules: true,
        preserveModulesRoot: epRoot,
        sourcemap: false,
        entryFileNames: ({ facadeModuleId }) => {
          const entryName = facadeModuleId
            ? moduleInputs.entryNames.get(normalizePath(facadeModuleId))
            : undefined
          return entryName
            ? `${entryName}.${config.ext}`
            : `[name].${config.ext}`
        },
      }
    })
  )
}

async function buildModulesStyles() {
  const files = excludeStandalonePackages(
    excludeFiles(
      await glob('**/style/(index|css).{js,ts,vue}', {
        cwd: pkgRoot,
        absolute: true,
        onlyFiles: true,
      })
    )
  )
  const moduleInputs = createDeterministicModuleInputs(files, pkgRoot, epRoot)
  const bundle = await rollup({
    input: [...moduleInputs.input],
    plugins: await getPlugins(),
    external: (id) => /\.(scss|css)$/.test(id),
    treeshake: false,
  })

  await writeBundles(
    bundle,
    buildConfigEntries.map(([module, config]): OutputOptions => {
      return {
        format: config.format,
        dir: config.output.path,
        exports: module === 'cjs' ? 'named' : undefined,
        preserveModules: true,
        preserveModulesRoot: epRoot,
        sourcemap: false,
        entryFileNames: ({ facadeModuleId }) => {
          const entryName = facadeModuleId
            ? moduleInputs.entryNames.get(normalizePath(facadeModuleId))
            : undefined
          return entryName
            ? `${entryName}.${config.ext}`
            : `[name].${config.ext}`
        },
      }
    })
  )
}

export const buildModules: TaskFunction = series(
  withTaskName('buildModulesComponents', buildModulesComponents),
  withTaskName('buildModulesStyles', buildModulesStyles)
)
