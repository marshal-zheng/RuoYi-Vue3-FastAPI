const path = require('path')
require('tsx/cjs')
const { defineConfig } = require('eslint-define-config')

const { uiPackageContractList } = require(path.resolve(
  __dirname,
  '../contracts/ui-package-contracts.ts'
))

const baseRestrictedImportPaths = [
  { name: 'lodash', message: 'Use @zxio/utils/lodash instead.' },
  { name: 'lodash-es', message: 'Use @zxio/utils/lodash instead.' },
]

const baseRestrictedImportPatterns = [
  {
    group: ['lodash/*', 'lodash-es/*'],
    message: 'Use @zxio/utils/lodash instead.',
  },
  {
    group: ['@zxio/**/internal', '@zxio/**/internal/**'],
    message: 'Use public entries such as @zxio/shared instead.',
  },
]

const managedUiBoundaryRoles = new Set([
  'hosted-ui-feature',
  'standalone-ui-feature',
  'headless-feature',
])

function createRestrictedImportGroup(prefix) {
  return [prefix, `${prefix}/*`]
}

function removeTransitionalPrefixes(forbidden = [], transitional = []) {
  return forbidden.filter((prefix) => !transitional.includes(prefix))
}

function buildManagedUiImportBoundaryOverrides() {
  return uiPackageContractList
    .filter((contract) => managedUiBoundaryRoles.has(contract.role))
    .map((contract) => {
      const forbiddenWorkspacePrefixes = removeTransitionalPrefixes(
        contract.importContract.forbiddenWorkspacePrefixes,
        contract.importContract.transitionalAllowedWorkspacePrefixes || []
      )
      const forbiddenThirdPartyPrefixes = removeTransitionalPrefixes(
        contract.importContract.forbiddenThirdPartyPrefixes || [],
        contract.importContract.transitionalAllowedThirdPartyPrefixes || []
      )

      const patterns = [...baseRestrictedImportPatterns]

      if (forbiddenWorkspacePrefixes.length > 0) {
        patterns.push({
          group: forbiddenWorkspacePrefixes.flatMap(
            createRestrictedImportGroup
          ),
          message: `Governed by ${contract.packageName} import contract. Use allowed public workspace entries only.`,
        })
      }

      if (forbiddenThirdPartyPrefixes.length > 0) {
        patterns.push({
          group: forbiddenThirdPartyPrefixes.flatMap(
            createRestrictedImportGroup
          ),
          message: `Governed by ${contract.packageName} import contract. This third-party dependency is not part of the public contract.`,
        })
      }

      return {
        files: [`${contract.workspaceDir}/**/*.{js,jsx,ts,tsx,vue}`],
        excludedFiles: [
          `${contract.workspaceDir}/**/__tests__/**`,
          `${contract.workspaceDir}/tests/**`,
          `${contract.workspaceDir}/specs/**`,
          `${contract.workspaceDir}/dist/**`,
          `${contract.workspaceDir}/vite.config.ts`,
        ],
        rules: {
          'no-restricted-imports': [
            'error',
            {
              paths: baseRestrictedImportPaths,
              patterns,
            },
          ],
        },
      }
    })
}

module.exports = defineConfig({
  ignorePatterns: ['.github/**/*'],
  env: {
    es6: true,
    browser: true,
    node: true,
  },
  plugins: ['@typescript-eslint', 'prettier', 'unicorn'],
  extends: [
    'eslint:recommended',
    'plugin:import-x/recommended',
    'plugin:eslint-comments/recommended',
    'plugin:jsonc/recommended-with-jsonc',
    'plugin:markdown/recommended',
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  settings: {
    'import-x/resolver': {
      node: { extensions: ['.js', '.mjs', '.ts', '.d.ts', '.tsx'] },
    },
  },
  overrides: [
    {
      files: ['*.json', '*.json5', '*.jsonc'],
      parser: 'jsonc-eslint-parser',
    },
    {
      files: ['**/__tests__/**', '**/*.{test,spec}.{js,jsx,ts,tsx,mjs,mts}'],
      rules: {
        'no-console': 'off',
        'vue/one-component-per-file': 'off',
      },
    },
    {
      files: ['package.json'],
      parser: 'jsonc-eslint-parser',
      rules: {
        'jsonc/sort-keys': 'off',
      },
    },
    {
      files: ['*.d.ts'],
      rules: {
        'import-x/no-duplicates': 'off',
      },
    },
    {
      files: ['*.js'],
      rules: {
        '@typescript-eslint/no-var-requires': 'off',
      },
    },
    {
      files: ['*.vue'],
      parser: 'vue-eslint-parser',
      parserOptions: {
        parser: '@typescript-eslint/parser',
        extraFileExtensions: ['.vue'],
        ecmaVersion: 'latest',
        ecmaFeatures: {
          jsx: true,
        },
      },
      rules: {
        'no-undef': 'off',
        '@typescript-eslint/consistent-type-imports': [
          'error',
          { disallowTypeAnnotations: false },
        ],
      },
    },
    {
      files: ['**/*.md/*.js', '**/*.md/*.ts'],
      rules: {
        'no-console': 'off',
        'import-x/no-unresolved': 'off',
        '@typescript-eslint/no-unused-vars': 'off',
      },
    },
    {
      files: [
        'docs/examples/**/*.{js,jsx,ts,tsx,vue}',
        'docs/en-US/**/*.md/*.{js,jsx,ts,tsx,vue}',
      ],
      rules: {
        'no-console': 'off',
        'import-x/no-unresolved': 'off',
        '@typescript-eslint/no-unused-vars': 'off',
        'no-restricted-imports': [
          'error',
          {
            paths: [{ name: '@zxio', message: 'Use @zxio/zxui instead.' }],
            patterns: [
              {
                group: [
                  '@zxio/*',
                  '!@zxio/icons-vue',
                  '!@zxio/theme-*',
                  '!@zxio/theme-*/*',
                  '!@zxio/zxui',
                  '!@zxio/keybindings',
                  '!@zxio/keybindings/*',
                  '!@zxio/text-editor',
                  '!@zxio/http',
                  '!@zxio/utils',
                  '!@zxio/drive',
                  '@zxio/zxui/es/*',
                  '!@zxio/zxui/es/locale',
                  '@zxio/zxui/lib/*',
                  '!@zxio/zxui/lib/locale',
                ],
                message: 'Use @zxio/zxui instead.',
              },
            ],
          },
        ],
      },
    },
    {
      files: [
        'internal/**/*.{js,ts}',
        'packages/constants/**/*.{js,ts}',
        'packages/locale/**/*.{js,ts}',
        'packages/test-utils/**/*.{js,ts}',
        'packages/theme-chalk/**/*.{js,ts}',
      ],
      rules: {
        'no-restricted-imports': [
          'error',
          {
            paths: [
              { name: 'lodash', message: 'Use @zxio/utils/lodash instead.' },
              { name: 'lodash-es', message: 'Use @zxio/utils/lodash instead.' },
              { name: '@zxio/zxui', message: 'Use @zxio/* instead.' },
            ],
            patterns: [
              {
                group: ['lodash/*', 'lodash-es/*'],
                message: 'Use @zxio/utils/lodash instead.',
              },
              {
                group: ['@zxio/zxui/*'],
                message: 'Use @zxio/* instead.',
              },
              {
                group: [
                  '@zxio/components',
                  '@zxio/constants',
                  '@zxio/directives',
                  '@zxio/hooks',
                  '@zxio/locale',
                  '@zxio/test-utils',
                  '@zxio/theme-chalk',
                  '@zxio/utils',
                  '@zxio/zxui',
                ],
                message:
                  'Please do not use this dependency in the current file.',
              },
            ],
          },
        ],
      },
    },
    {
      files: [
        'packages/directives/**/*.{js,jsx,ts,tsx,vue}',
        'packages/hooks/**/*.{js,jsx,ts,tsx,vue}',
        'packages/utils/**/*.{js,jsx,ts,tsx,vue}',
      ],
      rules: {
        'no-restricted-imports': [
          'error',
          {
            paths: [
              { name: 'lodash', message: 'Use @zxio/utils/lodash instead.' },
              { name: 'lodash-es', message: 'Use @zxio/utils/lodash instead.' },
              { name: '@zxio/zxui', message: 'Use @zxio/* instead.' },
            ],
            patterns: [
              {
                group: ['lodash/*', 'lodash-es/*'],
                message: 'Use @zxio/utils/lodash instead.',
              },
              {
                group: ['@zxio/zxui/*'],
                message: 'Use @zxio/* instead.',
              },
              {
                group: [
                  '@zxio/components',
                  '@zxio/theme-chalk',
                  '@zxio/build',
                  '@zxio/build-constants',
                  '@zxio/build-utils',
                  '@zxio/eslint-config',
                  '@zxio/zxui',
                ],
                message:
                  'Please do not use this dependency in the current file.',
              },
            ],
          },
        ],
      },
    },
    {
      files: [
        'packages/components/**/*.{js,jsx,ts,tsx,vue}',
        'packages/zxui/**/*.{js,jsx,ts,tsx,vue}',
      ],
      rules: {
        'no-restricted-imports': [
          'error',
          {
            paths: [
              { name: 'lodash', message: 'Use @zxio/utils/lodash instead.' },
              { name: 'lodash-es', message: 'Use @zxio/utils/lodash instead.' },
              { name: '@zxio/zxui', message: 'Use @zxio/* instead.' },
            ],
            patterns: [
              {
                group: ['lodash/*', 'lodash-es/*'],
                message: 'Use @zxio/utils/lodash instead.',
              },
              {
                group: ['@zxio/zxui/*'],
                message: 'Use @zxio/* instead.',
              },
              {
                group: [
                  '@zxio/theme-chalk/*',
                  '!@zxio/theme-chalk/button.css',
                  '!@zxio/theme-chalk/dialog.css',
                  '!@zxio/theme-chalk/date-picker.css',
                  '!@zxio/theme-chalk/icon.css',
                  '!@zxio/theme-chalk/input.css',
                  '!@zxio/theme-chalk/input-number.css',
                  '!@zxio/theme-chalk/select.css',
                  '!@zxio/theme-chalk/tag.css',
                  '!@zxio/theme-chalk/tooltip-or-popover.css',
                ],
                message:
                  'Use @zxio/theme-chalk or a documented component CSS entry.',
              },
              {
                group: [
                  '@zxio/build',
                  '@zxio/build-constants',
                  '@zxio/build-utils',
                  '@zxio/eslint-config',
                ],
                message:
                  'Please do not use this dependency in the current file.',
              },
            ],
          },
        ],
      },
    },
    ...buildManagedUiImportBoundaryOverrides(),
  ],
  rules: {
    // js/ts
    camelcase: ['error', { properties: 'never' }],
    'no-console': ['warn', { allow: ['error'] }],
    'no-debugger': 'warn',
    'no-constant-condition': ['error', { checkLoops: false }],
    'no-restricted-syntax': ['error', 'LabeledStatement', 'WithStatement'],
    'no-return-await': 'error',
    'no-var': 'error',
    'no-empty': ['error', { allowEmptyCatch: true }],
    'prefer-const': [
      'warn',
      { destructuring: 'all', ignoreReadBeforeAssign: true },
    ],
    'prefer-arrow-callback': [
      'error',
      { allowNamedFunctions: false, allowUnboundThis: true },
    ],
    'object-shorthand': [
      'error',
      'always',
      { ignoreConstructors: false, avoidQuotes: true },
    ],
    'prefer-rest-params': 'error',
    'prefer-spread': 'error',
    'prefer-template': 'error',

    'no-redeclare': 'off',
    '@typescript-eslint/no-redeclare': 'error',

    // best-practice
    'array-callback-return': 'error',
    'block-scoped-var': 'error',
    'no-alert': 'warn',
    'no-case-declarations': 'error',
    'no-multi-str': 'error',
    'no-with': 'error',
    'no-void': 'error',

    'sort-imports': [
      'warn',
      {
        ignoreCase: false,
        ignoreDeclarationSort: true,
        ignoreMemberSort: false,
        memberSyntaxSortOrder: ['none', 'all', 'multiple', 'single'],
        allowSeparatedGroups: false,
      },
    ],

    // stylistic-issues
    'prefer-exponentiation-operator': 'error',

    // ts
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-non-null-assertion': 'off',
    '@typescript-eslint/no-non-null-asserted-optional-chain': 'off',
    '@typescript-eslint/ban-ts-comment': ['off', { 'ts-ignore': false }],
    '@typescript-eslint/no-require-imports': 'off',
    '@typescript-eslint/no-unused-expressions': 'off',
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],

    // vue
    'vue/no-v-html': 'off',
    'vue/require-default-prop': 'off',
    'vue/require-explicit-emits': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/prefer-import-from-vue': 'off',
    'vue/no-v-text-v-html-on-component': 'off',
    'vue/padding-line-between-blocks': ['warn', 'always'],
    'vue/html-self-closing': [
      'error',
      {
        html: {
          void: 'always',
          normal: 'always',
          component: 'always',
        },
        svg: 'always',
        math: 'always',
      },
    ],

    // prettier
    'prettier/prettier': 'error',

    // import
    'import-x/first': 'error',
    'import-x/no-duplicates': 'error',
    'import-x/order': [
      'error',
      {
        groups: [
          'builtin',
          ['external', 'internal', 'parent', 'sibling', 'index', 'object'],
          'type',
        ],
        pathGroups: [
          {
            pattern: 'vue',
            group: 'external',
            position: 'before',
          },
          {
            pattern: '@vue/**',
            group: 'external',
            position: 'before',
          },
          {
            pattern: '@zxio/**',
            group: 'internal',
          },
        ],
        pathGroupsExcludedImportTypes: ['type'],
        sortTypesGroup: true,
        'newlines-between': 'never',
        'newlines-between-types': 'always',
      },
    ],
    'import-x/no-unresolved': 'off',
    'import-x/namespace': 'off',
    'import-x/default': 'off',
    'import-x/no-named-as-default': 'off',
    'import-x/no-named-as-default-member': 'off',
    'import-x/named': 'off',
    'import-x/newline-after-import': ['error', { count: 1 }],
    'no-restricted-imports': [
      'error',
      {
        paths: baseRestrictedImportPaths,
        patterns: baseRestrictedImportPatterns,
      },
    ],

    // eslint-plugin-eslint-comments
    'eslint-comments/disable-enable-pair': ['error', { allowWholeFile: true }],

    // unicorn
    'unicorn/custom-error-definition': 'error',
    'unicorn/error-message': 'error',
    'unicorn/escape-case': 'error',
    'unicorn/import-index': 'error',
    'unicorn/new-for-builtins': 'error',
    'unicorn/no-array-method-this-argument': 'error',
    'unicorn/no-array-push-push': 'error',
    'unicorn/no-console-spaces': 'error',
    'unicorn/no-for-loop': 'error',
    'unicorn/no-hex-escape': 'error',
    'unicorn/no-instanceof-array': 'error',
    'unicorn/no-invalid-remove-event-listener': 'error',
    'unicorn/no-new-array': 'error',
    'unicorn/no-new-buffer': 'error',
    'unicorn/no-unsafe-regex': 'off',
    'unicorn/number-literal-case': 'error',
    'unicorn/prefer-array-find': 'error',
    'unicorn/prefer-array-flat-map': 'error',
    'unicorn/prefer-array-index-of': 'error',
    'unicorn/prefer-array-some': 'error',
    'unicorn/prefer-date-now': 'error',
    'unicorn/prefer-dom-node-dataset': 'error',
    'unicorn/prefer-includes': 'error',
    'unicorn/prefer-keyboard-event-key': 'error',
    'unicorn/prefer-math-trunc': 'error',
    'unicorn/prefer-modern-dom-apis': 'error',
    'unicorn/prefer-negative-index': 'error',
    'unicorn/prefer-number-properties': 'error',
    'unicorn/prefer-optional-catch-binding': 'error',
    'unicorn/prefer-prototype-methods': 'error',
    'unicorn/prefer-query-selector': 'error',
    'unicorn/prefer-reflect-apply': 'error',
    'unicorn/prefer-string-slice': 'error',
    'unicorn/prefer-string-starts-ends-with': 'error',
    'unicorn/prefer-string-trim-start-end': 'error',
    'unicorn/prefer-type-error': 'error',
    'unicorn/throw-new-error': 'error',
  },
})
