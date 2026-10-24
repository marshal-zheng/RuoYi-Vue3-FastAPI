import { createRequire } from 'node:module'

const require = createRequire('/Users/hqz/Downloads/element-plus/packages/components/package.json')
const { createSSRApp, h } = require('vue')
const { renderToString } = require('vue/server-renderer')
const { ElInputNumber } = require('element-plus')
const html = await renderToString(createSSRApp({
  render: () => h(ElInputNumber, {
    modelValue: 1,
    'aria-label': 'Reading',
    'aria-invalid': 'true',
    'aria-describedby': 'reading-error',
  }),
}))
const root = html.match(/<div[^>]*>/)?.[0]
const input = html.match(/<input[^>]*>/)?.[0]
if (!root?.includes('aria-invalid="true"') || !root.includes('aria-describedby="reading-error"'))
  throw new Error('Expected the accessibility attributes on the current root wrapper')
if (!input || input.includes('aria-invalid') || input.includes('aria-describedby'))
  throw new Error('The installed dependency no longer reproduces the reported missing input attributes')
console.log(JSON.stringify({
  scope: 'Real installed Element Plus 2.13.0 SSR. Actual attribute placement is verified; browser/screen-reader behavior is not tested.',
  elementPlus: require('element-plus/package.json').version,
  node: process.version,
  root,
  input,
}, null, 2))
