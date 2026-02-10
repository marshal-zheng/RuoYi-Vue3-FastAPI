import { defineConfig, loadEnv } from 'vite'
import type { UserConfig, ConfigEnv, Alias } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import createVitePlugins from './vite/plugins'

const baseUrl = 'http://127.0.0.1:8088'

// ZXUI 本地直连时需要排除预构建的包
const zxuiExcludeDeps = [
  '@zxio/zxui',
  '@zxio/components',
  '@zxio/utils',
  '@zxio/hooks',
  '@zxio/constants',
  '@zxio/shared',
  '@zxio/types',
  '@zxio/tokens',
  '@zxio/chart',
  '@zxio/http',
  '@zxio/text-editor',
  '@zxio/theme-chalk',
]

// 生成 ZXUI 本地直连别名配置
function createZxuiLocalAlias(localPath: string): Alias[] {
  return [
    // 直连 ZXUI 入口（全量安装）
    { find: /^@zxio\/zxui$/, replacement: `${localPath}/zxui/index.ts` },
    // 兼容 es/lib 子路径（若业务有使用 @zxio/zxui/es/... 或 lib/...）
    { find: /^@zxio\/zxui\/(es|lib)\/(.*)$/, replacement: `${localPath}/$2` },
    // 样式相关
    { find: '@zxio/zxui/theme-chalk', replacement: `${localPath}/theme-chalk` },
    { find: '@zxio/theme-chalk', replacement: `${localPath}/theme-chalk` },
    // 直连各子包（按需引用）
    { find: '@zxio/components', replacement: `${localPath}/components` },
    { find: '@zxio/utils', replacement: `${localPath}/utils` },
    { find: '@zxio/hooks', replacement: `${localPath}/hooks` },
    { find: '@zxio/constants', replacement: `${localPath}/constants` },
    { find: '@zxio/shared', replacement: `${localPath}/shared` },
    { find: '@zxio/types', replacement: `${localPath}/types` },
    { find: '@zxio/tokens', replacement: `${localPath}/tokens` },
    { find: '@zxio/chart', replacement: `${localPath}/chart` },
    { find: '@zxio/http', replacement: `${localPath}/http` },
    { find: '@zxio/text-editor', replacement: `${localPath}/text-editor` },
  ]
}

// https://vitejs.dev/config/
export default defineConfig(({ mode, command }: ConfigEnv): UserConfig => {
  const env = loadEnv(mode, process.cwd())
  const { VITE_APP_ENV, VITE_ZXUI_LOCAL, VITE_ZXUI_LOCAL_PATH } = env
  
  // 测试环境配置
  const isTest = mode === 'test' || process.env.NODE_ENV === 'test'
  
  // 是否启用 ZXUI 本地直连模式（仅开发环境有效）
  const useZxuiLocal = command === 'serve' && VITE_ZXUI_LOCAL === 'true'
  
  // ZXUI 本地直连别名
  const zxuiLocalAlias = useZxuiLocal ? createZxuiLocalAlias(VITE_ZXUI_LOCAL_PATH) : []
  
  if (useZxuiLocal) {
    console.log('\n🔗 ZXUI 本地直连模式已启用')
    console.log(`   路径: ${VITE_ZXUI_LOCAL_PATH}\n`)
  }

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
      '/dev-api': {
        target: baseUrl,
        changeOrigin: true,
        ws: true, // 支持 WebSocket 代理
        // 将 /dev-api 重写为空（开发环境代理）
        rewrite: (p) => p.replace(/^\/dev-api/, '')
      }
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
