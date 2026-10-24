import { createRenderer, defineComponent, h, nextTick } from '/Users/hqz/Downloads/element-plus/node_modules/vue/index.mjs'
import fcModule from '/Users/hqz/Downloads/element-plus/packages/schema-form/node_modules/@form-create/element-ui/dist/form-create.min.js'
import { createSession } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/session.ts'
const formCreate = (fcModule as any).default || fcModule
const node = (type: string, text = '') => ({ type, text, parent: null as any, children: [] as any[], props: {} as any })
const renderer = createRenderer({
  createElement: (type) => node(type), createText: (text) => node('#text', text), createComment: (text) => node('#comment', text),
  setText: (el: any,text) => { el.text=text }, setElementText: (el: any,text) => { el.text=text },
  parentNode: (el:any) => el.parent, nextSibling: (el:any) => el.parent?.children[el.parent.children.indexOf(el)+1] || null,
  insert: (el:any,parent:any,anchor:any=null) => { if(el.parent){const i=el.parent.children.indexOf(el);if(i>=0)el.parent.children.splice(i,1)} el.parent=parent; const i=anchor?parent.children.indexOf(anchor):-1; if(i<0)parent.children.push(el);else parent.children.splice(i,0,el)},
  remove: (el:any) => {if(el.parent){const i=el.parent.children.indexOf(el);if(i>=0)el.parent.children.splice(i,1);el.parent=null}},
  patchProp: (el:any,key,prev,next) => {el.props[key]=next},
})
const Stub = defineComponent({ setup(_, {slots,expose}) { expose({validate: async()=>true,clearValidate(){}});return ()=>h('div', slots.default?.())} })
const Engine = formCreate.factory()
for(const n of ['ElForm','ElFormItem','ElRow','ElCol','ElButton','ElPopover','ElTooltip','ElIcon','Text'])Engine.component(n, Stub)
const rules = [{type:'Text',field:'name',title:'Name',wrap:{labelWidth:'200px', class:'business-wrap'}}]
let saves = 0
const session = createSession({name:'initial'}, async()=> ++saves === 1 ? ({ok:false,issues:[{field:'name',message:'duplicate'}]}) : ({ok:true}))
let api: any
const App = defineComponent({setup(){return ()=>h(Engine,{key:session.key.value,rule:rules,option:{submitBtn:false,resetBtn:false},'onUpdate:api':(a:any)=>{api=a;session.attach(a)},'onUpdate:modelValue':session.observe})}})
async function main(){
 const app=renderer.createApp(App);app.config.warnHandler=()=>{};app.mount(node('root'))
 await nextTick();await nextTick()
 console.log('initial',JSON.stringify({read:session.read(),wrap:api.getRule('name').wrap,rulesWrap:rules[0].wrap}))
 await session.submit();await nextTick()
 console.log('server error',JSON.stringify({wrap:api.getRule('name').wrap,rulesWrap:rules[0].wrap,issues:session.issues.value}))
 session.reset();await nextTick();await nextTick()
 console.log('after reset',JSON.stringify({wrap:api.getRule('name').wrap,rulesWrap:rules[0].wrap,issues:session.issues.value,dirty:session.dirty.value}))
 api.setValue('name','edited after reset');await nextTick();await nextTick()
 console.log('edited after reset',JSON.stringify({wrap:api.getRule('name').wrap,issues:session.issues.value,read:session.read()}))
 const result = await session.submit();await nextTick()
 console.log('saved after reset',JSON.stringify({result,wrap:api.getRule('name').wrap,issues:session.issues.value,status:session.status.value,dirty:session.dirty.value}))
 app.unmount()
}
main().catch(console.error)
