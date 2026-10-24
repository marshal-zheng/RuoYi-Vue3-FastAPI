import { createRenderer, defineComponent, h, nextTick, reactive } from '/Users/hqz/Downloads/element-plus/node_modules/vue/index.mjs'
import fcModule from '/Users/hqz/Downloads/element-plus/packages/schema-form/node_modules/@form-create/element-ui/dist/form-create.min.js'
const formCreate = (fcModule as any).default || fcModule
import { strict as assert } from 'node:assert'
import { performance } from 'node:perf_hooks'
import { createSession } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/session'

import type { Values } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/types'
import type { Api, Rule } from '@form-create/element-ui'
import type { ArrayKey, Save } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/form-create/types'

type Node = { parent: Node | null; children: Node[] }
const node = (): Node => ({ parent: null, children: [] })
const renderer = createRenderer<Node, Node>({
  createElement: node,
  createText: node,
  createComment: node,
  setText() {},
  setElementText() {},
  patchProp() {},
  parentNode: (el) => el.parent,
  nextSibling: (el) =>
    el.parent?.children[el.parent.children.indexOf(el) + 1] ?? null,
  insert(el, parent, anchor) {
    if (el.parent) el.parent.children.splice(el.parent.children.indexOf(el), 1)
    el.parent = parent
    const index = anchor ? parent.children.indexOf(anchor) : -1
    if (index < 0) parent.children.push(el)
    else parent.children.splice(index, 0, el)
  },
  remove(el) {
    if (el.parent) el.parent.children.splice(el.parent.children.indexOf(el), 1)
    el.parent = null
  },
})
const Stub = defineComponent({
  setup(_, { slots, expose }) {
    expose({ validate: async () => true, clearValidate() {} })
    return () => h('div', slots.default?.())
  },
})
async function mount(
  save: Save,
  initial: Values = { name: 'initial' },
  customRules?: Rule[],
  arrayKeys: ArrayKey[] = []
) {
  const Engine = formCreate.factory()
  for (const name of [
    'ElForm',
    'ElFormItem',
    'ElRow',
    'ElCol',
    'ElButton',
    'Text',
  ])
    Engine.component(name, Stub)
  const rules = reactive<Rule[]>(
    customRules ?? [
      {
        type: 'Text',
        field: 'name',
        title: 'Name',
        wrap: { labelWidth: '200px', class: 'business-wrap' },
      },
    ]
  )
  const session = createSession(initial, save, undefined, arrayKeys)
  let api!: Api
  const app = renderer.createApp(
    defineComponent({
      setup: () => () =>
        h(Engine, {
          key: session.key.value,
          rule: rules,
          option: { submitBtn: false, resetBtn: false },
          'onUpdate:api': (value: Api) => {
            api = value
            session.attach(value)
          },
          'onUpdate:modelValue': session.observe,
        }),
    })
  )
  app.config.warnHandler = () => {}
  app.mount(node())
  await nextTick()
  return {
    session,
    api: () => api,
    stop: () => {
      app.unmount()
      session.dispose()
    },
  }
}


async function main() {
  const results = []
  const percentile = (xs: number[]) => {
    const values = [...xs].sort((a,b)=>a-b)
    return {samples: values.length, p50ms: +values[Math.floor(values.length*.5)].toFixed(3), p95ms: +values[Math.floor(values.length*.95)].toFixed(3)}
  }
  for (const count of [50, 200]) {
    const rows = Array.from({length:count}, (_,i)=>({id:`row-${i}`,name:`Item ${i}`,qty:1,unit:'kg',price:10.5,remark:'x'.repeat(100)}))
    const target = count - 1
    const start = performance.now()
    const form = await mount(async () => ({ok:false,issues:[{path:['rows', target, 'name'],message:'target row error'}]}), {rows}, [{type:'group',field:'rows',props:{rule:Object.keys(rows[0]).map(field=>({type:'Text',field}))}}], [{path:['rows'],key:'id'}])
    await nextTick(); await nextTick()
    const mountMs = performance.now() - start
    try {
      const children = form.api().getSubForm('rows') as Api[]
      assert.equal(children.length, count)
      const edit: number[] = [], read: number[] = [], validate: number[] = []
      for (let i = 0; i < 13; i++) {
        let time = performance.now()
        children[target].setValue('remark', `edit-${i}`+'x'.repeat(100))
        await nextTick(); await nextTick()
        void form.session.dirty.value
        const editMs = performance.now()-time
        time = performance.now()
        const data = form.api().formData()
        const readMs = performance.now()-time
        assert.equal(data.rows[target].remark, `edit-${i}`+'x'.repeat(100))
        time = performance.now()
        await form.api().validate()
        const validateMs = performance.now()-time
        if (i >= 3) {edit.push(editMs);read.push(readMs);validate.push(validateMs)}
      }
      const errorStart = performance.now()
      assert.equal(await form.session.submit(), false)
      await nextTick()
      const errorMs = performance.now()-errorStart
      assert.equal((children[target].getRule('name')!.wrap as any).error, 'target row error')
      assert.equal((children[0].getRule('name')!.wrap as any)?.error, undefined)
      assert.deepEqual(form.session.issues.value[0].path, ['rows',target,'name'])
      results.push({rows:count,fieldsPerRow:6,bytes:Buffer.byteLength(JSON.stringify(form.api().formData())),mountMs:+mountMs.toFixed(3),editIncludingVueFlushAndSessionObservation:percentile(edit),fullFormData:percentile(read),validateDispatchToStub:percentile(validate),submitWithNestedServerIssueMs:+errorMs.toFixed(3),targetRowCorrect:true,untargetedFirstRowClean:true})
    } finally {form.stop()}
  }
  console.log(JSON.stringify({node:process.version,scope:'Real FormCreate 3.3.5 native group + Vue memory renderer + current schema session; ElForm/controls are stubs. validate measures native traversal/dispatch to successful stub validators, NOT real Element Plus validators. No browser DOM, layout, paint, network or user latency.',warmup:3,samples:10,results},null,2))
}
main().catch(error=>{console.error(error);process.exitCode=1})
