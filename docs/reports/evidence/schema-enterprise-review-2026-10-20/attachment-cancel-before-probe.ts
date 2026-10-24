import { readFileSync } from 'node:fs'
import { strict as assert } from 'node:assert'
import * as Vue from '/Users/hqz/Downloads/element-plus/node_modules/vue/index.mjs'
import * as compiler from '/Users/hqz/Downloads/element-plus/node_modules/vue/compiler-sfc/index.js'
import ts from '/Users/hqz/Downloads/element-plus/node_modules/typescript/lib/typescript.js'
import { equal } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/json.ts'
const {createRenderer,defineComponent,h,ref,nextTick}=Vue
let uploadProps:any
const Upload=defineComponent({props:['modelValue','httpRequest','beforeRemove'],setup(props){return()=>{uploadProps=props;return h('div')}}})
const filename='/Users/hqz/Downloads/element-plus/docs/research/schema-form-pilot/pilot/inspection/AttachmentField.vue'
const {descriptor}=compiler.parse(readFileSync(filename,'utf8'),{filename})
const script=compiler.compileScript(descriptor,{id:'probe',inlineTemplate:true})
const output=ts.transpileModule(script.content,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}})
const loaded={exports:{}};new Function('require','module','exports',output.outputText)((id:string)=>id==='vue'?Vue:id==='@zxio/zxui/upload'?{ZxUpload:Upload}:id==='@zxio/schema-form'?{equal}:(()=>{throw new Error(id)})(),loaded,loaded.exports)
const Field=(loaded.exports as any).default
const node=()=>({parent:null as any,children:[] as any[]})
const renderer=createRenderer({createElement:node,createText:node,createComment:node,setText(){},setElementText(){},patchProp(){},parentNode:(e:any)=>e.parent,nextSibling:()=>null,insert(e:any,p:any){e.parent=p;p.children.push(e)},remove(e:any){if(e.parent){const i=e.parent.children.indexOf(e);if(i>=0)e.parent.children.splice(i,1)}e.parent=null}})
async function main(){
 const evidence=[]
 for(const action of ['remove','replace']){
  let signal:AbortSignal|undefined;let state:any;const values=ref<any[]>([])
  const app=renderer.createApp(defineComponent({setup:()=>()=>h(Field,{modelValue:values.value,upload:(_:unknown,s:AbortSignal)=>{signal=s;return new Promise(()=>{})},'onEdit-state':(s:any)=>state=s})}));app.mount(node());await nextTick()
  uploadProps.httpRequest({file:{uid:100}});assert.equal(state.pending,true)
  if(action==='remove')uploadProps.beforeRemove({uid:100})
  else values.value=[{id:'server',name:'accepted.txt',url:''}]
  await nextTick();await nextTick()
  assert.equal(signal!.aborted,true);assert.equal(state.pending,true);assert.equal(state.blocking.length,1)
  evidence.push({action,aborted:signal!.aborted,stateAfterCancel:state})
  app.unmount()
 }
 console.log(JSON.stringify({scope:'actual AttachmentField SFC compiled; Vue memory renderer; ZxUpload stub; upload promise ignores AbortSignal and remains pending',evidence},null,2))
}
main().catch(e=>{console.error(e);process.exitCode=1})
