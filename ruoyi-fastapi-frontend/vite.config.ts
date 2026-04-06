import { defineConfig, loadEnv } from 'vite'
import type { UserConfig, ConfigEnv, Alias } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import createVitePlugins from './vite/plugins'

const baseUrl = 'http://127.0.0.1:8088'

function normalizeApiPrefix(value?: string): string {
  if (!value) return '/api'
  const withLeadingSlash = value.startsWith('/') ? value : `/${value}`
  return withLeadingSlash.replace(/\/+$/, '') || '/api'
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// ZXUI 本地直连时需要排除预构建的包
const zxuiExcludeDeps = [
  '@zxio/zxui',
  '@zxio/components',
  '@zxio/constants',
  '@zxio/hooks',
  '@zxio/shared',
  '@zxio/theme-chalk',
  '@zxio/tokens',
  '@zxio/types',
  '@zxio/utils',
]

// 生成 ZXUI 本地直连别名配置（与 ZXUI 官方 host contract 对齐）
function createZxuiLocalAlias(repoRoot: string): Alias[] {
  const packagesRoot = path.resolve(repoRoot, 'packages')

  return [
    {
      find: /^@zxio\/theme-default\/theme\.css$/,
      replacement: path.resolve(packagesRoot, 'theme-default/theme.css'),
    },
    {
      find: /^@zxio\/zxui\/style$/,
      replacement: path.resolve(packagesRoot, 'zxui/style.ts'),
    },
    {
      find: /^@zxio\/zxui\/style\.css$/,
      replacement: path.resolve(packagesRoot, 'zxui/style/index.css'),
    },
    {
      find: /^@zxio\/zxui$/,
      replacement: path.resolve(packagesRoot, 'zxui/index.ts'),
    },
    {
      find: /^@zxio\/zxui\/(.*)$/,
      replacement: `${path.resolve(packagesRoot, 'zxui')}/$1`,
    },
    {
      find: /^@zxio\/theme-chalk\/src\/(.*)$/,
      replacement: `${path.resolve(packagesRoot, 'theme-chalk/src')}/$1`,
    },
    {
      find: /^@zxio\/theme-chalk\/(.+\.css)$/,
      replacement: `${path.resolve(packagesRoot, 'theme-chalk/dist')}/$1`,
    },
    {
      find: /^@zxio\/tokens\/tokens\.css$/,
      replacement: path.resolve(packagesRoot, 'tokens/tokens.css'),
    },
    {
      find: /^@zxio\/(components|constants|hooks|shared|tokens|types|utils)$/,
      replacement: `${packagesRoot}/$1`,
    },
    {
      find: /^@zxio\/(components|constants|hooks|shared|tokens|types|utils)\/(.*)$/,
      replacement: `${packagesRoot}/$1/$2`,
    },
  ]
}

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }: ConfigEnv): UserConfig => {
  const env = loadEnv(mode, process.cwd())
  const { VITE_APP_ENV, VITE_ZXUI_LOCAL, VITE_ZXIO_REPO_ROOT } = env
  const apiPrefix = normalizeApiPrefix(env.VITE_APP_BASE_API)
  
  // 测试环境配置
  const isTest = mode === 'test' || process.env.NODE_ENV === 'test'
  
  // 是否启用 ZXUI 本地直连模式（仅开发环境有效）
  const useZxuiLocal = command === 'serve' && VITE_ZXUI_LOCAL === 'true'

  if (useZxuiLocal && !VITE_ZXIO_REPO_ROOT) {
    throw new Error(
      'ZXUI 本地直连模式已启用，但缺少 VITE_ZXIO_REPO_ROOT 环境变量。' +
      '请在 .env.development 或 .env.local 中设置 VITE_ZXIO_REPO_ROOT 为 ZXUI monorepo 绝对路径。'
    )
  }
  
  // ZXUI 本地直连别名
  const zxuiLocalAlias = useZxuiLocal ? createZxuiLocalAlias(VITE_ZXIO_REPO_ROOT) : []

  // 基础别名配置
  const baseAlias: Alias[] = [
    // 设置路径
    { find: '~', replacement: path.resolve(__dirname, './') },
    // 设置别名
    { find: '@', replacement: path.resolve(__dirname, './src') },
  ]
  
  return {
    // 部署生产环境和开发环境下的URL。
    // 默认情况下，vite 会假设你的应用是被部署在一个域名的根路径上
    // 例如 https://www.example.com/。如果应用被部署在一个子路径上，你就需要用这个选项指定这个子路径。例如，如果你的应用被部署在 https://www.example.com/admin/，则设置 baseUrl 为 /admin/。
    base: VITE_APP_ENV === 'production' ? '/' : '/',
    plugins: isTest ? [] : [
      tailwindcss(),
      ...createVitePlugins(env, command === 'build')
    ],
    resolve: {
      // https://cn.vitejs.dev/config/#resolve-alias
      // 本地直连模式时，ZXUI 别名放在前面优先匹配
      alias: useZxuiLocal ? [...zxuiLocalAlias, ...baseAlias] : baseAlias,
      // https://cn.vitejs.dev/config/#resolve-extensions
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    // vite 相关配置
    server: {
      port: 80,
      host: true,
      open: true,
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
      include: ['@iconify/iconify'],
      // 本地直连模式时排除 ZXUI 相关包的预构建
      exclude: useZxuiLocal ? zxuiExcludeDeps : []
    },
    //fix:error:stdin>:7356:1: warning: "@charset" must be the first rule in the file
    css: {
      postcss: './postcss.config.js'
    },
    // 构建配置
    build: {
      outDir: 'dist',
      emptyOutDir: true
    }
  }
})
