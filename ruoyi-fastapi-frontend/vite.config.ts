import { defineConfig, loadEnv } from 'vite'
import type { UserConfig, ConfigEnv } from 'vite'
import fs from 'fs'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import createVitePlugins from './vite/plugins'
import { zxuiSourceIntegrationPlugin, zxuiThemeDeploymentPlugin } from './vite/zxui-theme-packages'

const baseUrl = 'http://127.0.0.1:8088'

function normalizeApiPrefix(value?: string): string {
  if (!value) return '/api'
  const withLeadingSlash = value.startsWith('/') ? value : `/${value}`
  return withLeadingSlash.replace(/\/+$/, '') || '/api'
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }: ConfigEnv): UserConfig => {
  const env = loadEnv(mode, process.cwd())
  const { VITE_ZXUI_LOCAL, VITE_ZXIO_REPO_ROOT } = env
  const developmentEnv = mode === 'development' ? env : loadEnv('development', process.cwd())
  const apiPrefix = normalizeApiPrefix(env.VITE_APP_BASE_API)
  const isDemoOfflineBuild = mode === 'demo-offline'
  const buildOutDir = mode === 'demo-offline' ? 'dist-demo-offline' : 'dist'
  const developmentRepoRoot = developmentEnv.VITE_ZXIO_REPO_ROOT
  const explicitRepoRoot = VITE_ZXIO_REPO_ROOT
  const requestedZxuiLocal = VITE_ZXUI_LOCAL === 'true'
  const fallbackToDevelopmentZxui =
    command === 'build' &&
    isDemoOfflineBuild &&
    developmentEnv.VITE_ZXUI_LOCAL === 'true' &&
    !!developmentRepoRoot &&
    fs.existsSync(developmentRepoRoot)
  const effectiveZxuiRepoRoot = explicitRepoRoot || (fallbackToDevelopmentZxui ? developmentRepoRoot : '')
  // 测试环境配置
  const isTest = mode === 'test' || process.env.NODE_ENV === 'test'

  // 是否启用 ZXUI 本地直连模式
  // 1. 开发环境使用当前 mode 的显式配置
  // 2. demo-offline 构建时，如果本机开发环境已接入 ZXUI 本地仓库，则复用同一套源码，避免与 node_modules 产物不一致
  const useZxuiLocal =
    requestedZxuiLocal || fallbackToDevelopmentZxui

  if (command === 'build' && developmentEnv.VITE_ZXUI_LOCAL === 'true') {
    const repoRootHint = developmentEnv.VITE_ZXIO_REPO_ROOT || '(missing VITE_ZXIO_REPO_ROOT)'
    if (useZxuiLocal) {
      console.warn(
        `[vite] ${mode} 构建复用了 .env.development 的 ZXUI 本地直连配置（${repoRootHint}），` +
        '以避免 demo-offline 与开发模式落到不同的 ZXUI 产物。'
      )
    } else {
      console.warn(
        `[vite] 检测到 .env.development 启用了 ZXUI 本地直连（${repoRootHint}），` +
        `但当前 ${mode} 构建不会走本地源码，而是回退到 node_modules/@zxio/*。` +
        '如果 demo-offline 与开发模式表现不一致，请优先检查这个差异。'
      )
    }
  }

  if (useZxuiLocal && !effectiveZxuiRepoRoot) {
    throw new Error(
      'ZXUI 本地直连模式已启用，但缺少 VITE_ZXIO_REPO_ROOT 环境变量。' +
      '请在 .env.development 或 .env.local 中设置 VITE_ZXIO_REPO_ROOT 为 ZXUI monorepo 绝对路径。'
    )
  }

  return {
    // 部署生产环境和开发环境下的URL。
    // 默认情况下，vite 会假设你的应用是被部署在一个域名的根路径上
    // 例如 https://www.example.com/。如果应用被部署在一个子路径上，你就需要用这个选项指定这个子路径。例如，如果你的应用被部署在 https://www.example.com/admin/，则设置 baseUrl 为 /admin/。
    base: isDemoOfflineBuild ? './' : '/',
    plugins: isTest ? [] : [
      ...(useZxuiLocal ? [zxuiSourceIntegrationPlugin(__dirname, effectiveZxuiRepoRoot)] : []),
      zxuiThemeDeploymentPlugin({ frontendRoot: __dirname, localRepoRoot: useZxuiLocal ? effectiveZxuiRepoRoot : undefined }),
      tailwindcss(),
      ...createVitePlugins(env, command === 'build')
    ],
    resolve: {
      dedupe: ['vue', 'element-plus', '@vue/runtime-core', '@vue/runtime-dom', '@vue/reactivity', '@vue/shared'],
      // https://cn.vitejs.dev/config/#resolve-alias
      // 本地直连模式时，ZXUI 别名放在前面优先匹配
      alias: [
        { find: '~', replacement: path.resolve(__dirname, './') },
        { find: '@', replacement: path.resolve(__dirname, './src') },
      ],
      // https://cn.vitejs.dev/config/#resolve-extensions
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    // vite 相关配置
    server: {
      port: 80,
      host: true,
      open: true,
      watch: {
        ignored: ['**/tests/**', '**/dist/**', '**/dist-demo-offline/**'],
      },
      proxy: {
        // https://cn.vitejs.dev/config/#server-proxy
        [apiPrefix]: {
          target: baseUrl,
          changeOrigin: true,
          ws: true, // 支持 WebSocket 代理
          // 将统一的 API 前缀重写为空，由后端直接处理真实路由
          rewrite: (p) => p.replace(new RegExp(`^${escapeRegExp(apiPrefix)}`), '') || '/',
        },
      }
    },
    optimizeDeps: {
      entries: ['index.html'],
      include: ['@iconify/iconify'],
      // ZXUI source dependency handling is owned by its public Vite plugin.
    },
    //fix:error:stdin>:7356:1: warning: "@charset" must be the first rule in the file
    css: {
      postcss: './postcss.config.js'
    },
    // 构建配置
    build: {
      outDir: buildOutDir,
      emptyOutDir: true
    }
  }
})
