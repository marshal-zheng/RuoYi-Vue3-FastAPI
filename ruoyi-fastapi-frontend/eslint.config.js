import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import vue from 'eslint-plugin-vue';
import vueParser from 'vue-eslint-parser';
import prettier from 'eslint-plugin-prettier';
import prettierConfig from 'eslint-config-prettier';
import globals from 'globals';

// Vue / vue-router / pinia 自动导入的全局变量（对应 unplugin-auto-import imports: ['vue','vue-router','pinia']）
const autoImportGlobals = {
  // Vue Composition API
  ref: 'readonly',
  reactive: 'readonly',
  computed: 'readonly',
  watch: 'readonly',
  watchEffect: 'readonly',
  watchPostEffect: 'readonly',
  watchSyncEffect: 'readonly',
  onMounted: 'readonly',
  onUnmounted: 'readonly',
  onBeforeMount: 'readonly',
  onBeforeUnmount: 'readonly',
  onUpdated: 'readonly',
  onBeforeUpdate: 'readonly',
  onActivated: 'readonly',
  onDeactivated: 'readonly',
  onErrorCaptured: 'readonly',
  onRenderTracked: 'readonly',
  onRenderTriggered: 'readonly',
  onServerPrefetch: 'readonly',
  nextTick: 'readonly',
  provide: 'readonly',
  inject: 'readonly',
  toRef: 'readonly',
  toRefs: 'readonly',
  toValue: 'readonly',
  unref: 'readonly',
  isRef: 'readonly',
  isProxy: 'readonly',
  isReactive: 'readonly',
  isReadonly: 'readonly',
  readonly: 'readonly',
  shallowRef: 'readonly',
  shallowReactive: 'readonly',
  shallowReadonly: 'readonly',
  triggerRef: 'readonly',
  customRef: 'readonly',
  markRaw: 'readonly',
  toRaw: 'readonly',
  effectScope: 'readonly',
  getCurrentScope: 'readonly',
  onScopeDispose: 'readonly',
  useAttrs: 'readonly',
  useSlots: 'readonly',
  useCssVars: 'readonly',
  useTemplateRef: 'readonly',
  // Vue defineXxx 宏（Vue SFC <script setup>）
  defineProps: 'readonly',
  defineEmits: 'readonly',
  defineExpose: 'readonly',
  defineOptions: 'readonly',
  defineSlots: 'readonly',
  defineModel: 'readonly',
  withDefaults: 'readonly',
  // vue-router
  useRouter: 'readonly',
  useRoute: 'readonly',
  useLink: 'readonly',
  onBeforeRouteLeave: 'readonly',
  onBeforeRouteUpdate: 'readonly',
  // pinia
  defineStore: 'readonly',
  storeToRefs: 'readonly',
  acceptHMRUpdate: 'readonly',
  getActivePinia: 'readonly',
  setActivePinia: 'readonly',
  createPinia: 'readonly',
  mapActions: 'readonly',
  mapGetters: 'readonly',
  mapState: 'readonly',
  mapStores: 'readonly',
  mapWritableState: 'readonly',
};

export default [
  // 忽略的文件和目录
  {
    ignores: [
      'node_modules/**',
      '.yarn/**',
      'dist/**',
      'build/**',
      '*.config.js',
      '*.config.ts',
      'vite.config.ts',
      'postcss.config.js',
      'tailwind.config.ts',
      '.env*',
      '.DS_Store',
      '*.log',
      '*.lock',
      'yarn.lock',
      'package-lock.json',
      '.temp/**',
      '.cache/**',
      '.vscode/**',
      '.idea/**',
      'public/**',
      'html/**',
    ],
  },
  
  // JavaScript/TypeScript 文件配置
  {
    files: ['**/*.{js,mjs,cjs,ts,tsx}'],
    languageOptions: {
      parser: typescriptParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module'
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...autoImportGlobals,
      }
    },
    plugins: {
      '@typescript-eslint': typescript,
      prettier
    },
    rules: {
      ...js.configs.recommended.rules,
      ...typescript.configs.recommended.rules,

      // TypeScript 相关规则
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-inferrable-types': 'off',
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/no-unused-expressions': 'warn',
      '@typescript-eslint/no-this-alias': 'warn',

      // TypeScript 已覆盖这些规则，禁用 ESLint 原版避免误报
      'no-undef': 'off',
      'no-redeclare': 'off',
      'no-unused-expressions': 'off',
      'no-prototype-builtins': 'off',
      'no-useless-escape': 'warn',
      'no-setter-return': 'warn',
      'no-empty': 'warn',

      // TypeScript recommended 中过于严格的规则降级
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/no-unsafe-function-type': 'warn',

      // 通用规则
      'no-console': 'warn',
      'no-debugger': 'warn',
      'no-unused-vars': 'off',
      'no-restricted-syntax': [
        'error',
        {
          selector: "AssignmentExpression[left.property.name='innerHTML']",
          message: '禁止直接写入 innerHTML，请使用安全渲染方案。',
        },
      ],
      
      // Prettier 相关
      'prettier/prettier': [
        'error',
        {
          singleQuote: true,
          trailingComma: 'es5',
          tabWidth: 2,
          semi: true,
          printWidth: 100
        }
      ]
    }
  },
  
  // Vue 文件配置
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: typescriptParser,
        ecmaVersion: 2020,
        sourceType: 'module',
        extraFileExtensions: ['.vue']
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...autoImportGlobals,
      }
    },
    plugins: {
      vue,
      '@typescript-eslint': typescript,
      prettier
    },
    rules: {
      // Vue 相关规则
      'vue/no-unused-vars': 'warn',
      'vue/no-v-html': 'error',
      'vue/require-default-prop': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/require-v-for-key': 'error',
      'vue/no-use-v-if-with-v-for': 'error',
      'no-restricted-syntax': [
        'error',
        {
          selector: "AssignmentExpression[left.property.name='innerHTML']",
          message: '禁止直接写入 innerHTML，请使用安全渲染方案。',
        },
      ],

      // TypeScript 已覆盖，禁用 ESLint 原版避免误报
      'no-undef': 'off',
      'no-redeclare': 'off',
      'no-unused-expressions': 'off',
      'no-prototype-builtins': 'off',
      'no-useless-escape': 'warn',
      'no-setter-return': 'warn',
      'no-empty': 'warn',

      // TypeScript recommended 中过于严格的规则降级
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/no-unsafe-function-type': 'warn',

      // TypeScript 相关规则
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      
      // Prettier 相关
      'prettier/prettier': [
        'error',
        {
          singleQuote: true,
          trailingComma: 'es5',
          tabWidth: 2,
          semi: true,
          printWidth: 100
        }
      ]
    }
  },
  
  // 应用 Prettier 配置
  prettierConfig
];
