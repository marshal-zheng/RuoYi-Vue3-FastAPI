const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { createServer, request: nodeRequest } = require('node:http');
const root = '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend';
const req = createRequire(path.join(root, 'package.json'));
const { JSDOM } = req('jsdom');
const ts = req('typescript');
const dom = new JSDOM('', { url: 'http://127.0.0.1:8088/' });
for (const key of ['window', 'document', 'location', 'XMLHttpRequest', 'FormData', 'File', 'Blob', 'FileReader', 'sessionStorage', 'localStorage']) {
  globalThis[key] = key === 'window' ? dom.window : dom.window[key];
}
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
const axios = req('axios').default;
const modules = new Map();
const messages = [];
const savedFiles = [];
const masks=[];
let nextSaveError;
let reloginPrompts = 0;
const mode = process.env.HTTP_PROBE_MODE || 'source';
const mocks = {
  'element-plus': { ElMessageBox: { alert() {} }, ElMessage: { error(message) { messages.push(message); } }, ElLoading: { service() { const mask={closed:0,close(){this.closed++;}};masks.push(mask);return mask; } } },
  'file-saver': { saveAs(blob, filename) { if(nextSaveError){const error=nextSaveError;nextSaveError=undefined;throw error;}savedFiles.push({blob, filename}); } },
  '@/router/history': { isHashRouteMode: () => false },
  '@/store/modules/user': { __esModule: true, default: () => ({ logOut: () => Promise.resolve() }) },
  '@/utils/feedback/presenter': {
    resolveFeedbackOptions: value => ({ mode: 'silent', ...value }),
    presentProblemFeedback: value => {if(value.feedback.mode==='auto')messages.push(value.problem.detail);},
    presentSuccessFeedback() {},
  },
  '@/utils/feedback/message': { showMessage: async () => { reloginPrompts++; return { ok: true, value: { close() {} } }; } },
  '@/utils/ruoyi': { blobValidate: blob => blob instanceof Blob && !blob.type.includes('json') },
};
function load(file) {
  if (file === '@zxio/http' && mode === 'source') return load('/Users/hqz/Downloads/element-plus/packages/http/src/index.ts');
  if (file in mocks) return mocks[file];
  let absolute;
  if (file.startsWith('@/')) absolute = path.join(root, 'src', file.slice(2));
  else if (file.startsWith('/')) absolute = file;
  else return req(file);
  if (!path.extname(absolute)) absolute = ['.ts', '.js', '/index.ts', '/index.js'].map(ext => absolute + ext).find(fs.existsSync);
  if (!absolute) throw Error('Cannot load ' + file);
  if (modules.has(absolute)) return modules.get(absolute).exports;
  const mod = {exports:{}};
  modules.set(absolute, mod);
  const input = fs.readFileSync(absolute, 'utf8').replaceAll('import.meta.env.VITE_APP_BASE_API', JSON.stringify('http://127.0.0.1:8088'));
  const output = ts.transpileModule(input, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
  const localRequire = id => load(id.startsWith('.') ? path.resolve(path.dirname(absolute), id) : id);
  vm.runInThisContext('(function(require,module,exports){' + output + '\n})', {filename:absolute})(localRequire, mod, mod.exports);
  return mod.exports;
}



mocks['@zxio/utils'] = load('/Users/hqz/Downloads/element-plus/packages/utils/public/helpers/object-utils.ts');
mocks['@/utils/ruoyi'] = load(root + '/src/utils/ruoyi.ts');



delete mocks['@/utils/feedback/presenter'];delete mocks['@/utils/feedback/message'];
for(const key of ['Element','SVGElement','Node'])globalThis[key]=dom.window[key];
const vue=req('vue');
mocks['@zxio/zxui']={
 useDialog:load('/Users/hqz/Downloads/element-plus/packages/components/hooks/use-dialog/index.ts').useDialog,
 useDrawer:load('/Users/hqz/Downloads/element-plus/packages/components/hooks/use-drawer/index.ts').useDrawer,
};
mocks['@/utils/dict']={useDict:()=>({sys_yes_no:vue.ref([]),sys_normal_disable:vue.ref([])})};
mocks[root+'/src/components/ui/FormDialog/FormGrid.vue']={__esModule:true,default:{render:()=>null}};
const {parse,compileScript}=req('@vue/compiler-sfc');
const {http,isRelogin,dismissReloginPrompt}=load('@/utils/http');
const auth=load('@/utils/auth'),login=load('@/api/login');
const configs=load('@/api/system/config'),dicts=load('@/api/system/dict/type'),depts=load('@/api/system/dept'),roles=load('@/api/system/role'),menus=load('@/api/system/menu');
const {HttpError,isAbortError}=load('@zxio/http');
const unhandled=[];process.on('unhandledRejection',error=>unhandled.push(String(error)));
let feedbackCalls=0;
const boundMessage=load('@/utils/feedback/message').bindMessageFeedback(()=>{feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const boundNotification=load('@/utils/feedback/notification').bindNotificationFeedback(()=>{feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const dir='/tmp/ruoyi-remaining-editor-reads',tag='erd'+Date.now().toString(36),pages=[],held=[],reads=[],results=[];
const outcome=task=>task.then(value=>({value}),error=>({error}));
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(predicate){const end=Date.now()+12000;while(!predicate()){if(Date.now()>end)throw Error('Timed out waiting for upstream response');await delay(5);}}
async function check(name,fn){const result={name,ok:true,...await fn()};results.push(result);console.log(JSON.stringify(result));}
function page(componentPath,kind){
 const descriptor=parse(fs.readFileSync(root+'/src/'+componentPath,'utf8')).descriptor;
 const script=compileScript(descriptor,{id:'actual-remaining-'+kind}).content;
 const output=ts.transpileModule(script,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
 const mod={exports:{}};vm.runInThisContext('(function(require,module,exports){'+output+'\n})',{filename:componentPath})(load,mod,mod.exports);
 const component=mod.exports.default,setup=component.setup;let bindings;
 component.setup=(props,context)=>{bindings=setup(props,context);return bindings;};component.render=()=>null;
 const events=[],app=vue.createApp(component,{save:data=>protocols.updateProtocol(data),sysShowHide:[],sysNormalDisable:[],onSuccess:()=>events.push('success'),onConfirm:()=>events.push('confirm')});
 app.config.globalProperties.useDict=()=>({sys_normal_disable:vue.ref([])});app.config.globalProperties.resetForm=()=>{};
 const host=document.createElement('div');document.body.append(host);app.mount(host);let disposed=false;
 const p={events,get b(){return bindings;},get state(){return bindings.drawer?.state||bindings.dataDialog?.state||bindings.state;},get props(){return bindings.drawer?bindings.drawer.drawerProps.value:bindings.dataDialog?bindings.dataDialog.dialogProps.value:bindings.dialogProps.value;},get loading(){return (bindings.drawerLoading||bindings.detailLoading).value;},get disabled(){return Boolean(p.props.okDisabled||p.loading||bindings.loadError.value);},async confirm(){return kind==='data'?bindings.submitForm():p.props.confirm(p.state.data);},exposed:{open:arg=>kind==='data'?bindings.openEditor(arg?.dictCode):bindings.openDrawer?bindings.openDrawer(arg):bindings.openDialog(arg),close:()=>kind==='data'?bindings.cancel():bindings.closeDrawer?bindings.closeDrawer():bindings.closeDialog()},dispose(){if(!disposed){app.unmount();host.remove();disposed=true;}}};
 if(kind==='data'){bindings.dataRef.value={validate:async()=>true};app._instance.refs={dataRef:bindings.dataRef.value};}
 pages.push(p);return p;
}
let viaGateway=false,invalidPrefix,interceptor,loggedIn=false,initial;
const unusedTargetUrl=url=>/^\/system\/(?:config\/\d+|dict\/type\/\d+|dept\/(?:\d+|list(?:\/exclude\/\d+)?)|role\/(?:\d+|deptTree\/\d+)|menu\/(?:treeselect|roleMenuTreeselect\/\d+))$/.test(url||'');
const gateway=createServer(async(incoming,res)=>{
 res.setHeader('Access-Control-Allow-Origin','http://127.0.0.1:8088');res.setHeader('Access-Control-Allow-Credentials','true');res.setHeader('Access-Control-Allow-Headers','Authorization, X-CSRF-Token, Content-Type');res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');
 if(incoming.method==='OPTIONS'){res.writeHead(204);res.end();return;}
 try{const upstream=await fetch('http://127.0.0.1:8088'+incoming.url,{headers:{Authorization:incoming.headers.authorization||''}});const bytes=Buffer.from(await upstream.arrayBuffer());res.statusCode=upstream.status;for(const key of ['content-type','x-request-id'])if(upstream.headers.get(key))res.setHeader(key,upstream.headers.get(key));held.push({url:incoming.url,status:upstream.status,release(){if(!res.destroyed&&!res.writableEnded)res.end(bytes);}});}catch(error){if(!res.destroyed){res.statusCode=502;res.end('{}');}}
});
async function unusedInventory(){return {config:await configs.listConfig({page:1,pageSize:10000}),dict:await dicts.listType({page:1,pageSize:10000}),dept:await depts.listDept(),role:await roles.listRole({page:1,pageSize:10000})};}
function flatten(nodes){return nodes.flatMap(node=>[node,...flatten(node.children||[])]);}
function originalError(error,status){assert.ok(error instanceof HttpError, 'Expected HttpError: '+String(error));assert.equal(error.status,status);assert.equal(error.problem.status,status);assert.equal(error.cause.config,error.config);assert.equal(error.cause.response,error.response);}
function handlers(file,names,context){const descriptor=parse(fs.readFileSync(root+'/src/'+file,'utf8')).descriptor;const ast=ts.createSourceFile(file+'.ts',descriptor.scriptSetup.content,ts.ScriptTarget.Latest,true,ts.ScriptKind.TS);const source=ast.statements.filter(n=>ts.isFunctionDeclaration(n)&&names.includes(n.name?.text)).map(n=>n.getText(ast)).join('\n');const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;return vm.runInNewContext(code+'\n({'+names.join(',')+'})',context);}

const posts=load('@/api/system/post'),notices=load('@/api/system/notice'),projects=load('@/api/project/project'),systemProjects=load('@/api/system/project'),protocols=load('@/api/protocol/protocol'),dataApi=load('@/api/system/dict/data'),users=load('@/api/system/user');
const targetUrl=url=>/^\/(?:system\/(?:menu\/(?:\d+|treeselect)|notice\/\d+|post\/\d+|dict\/data\/\d+|protocol\/\d+|user\/(?:\d+)?)|project\/\d+)$/.test(url||'');
mocks['@/components/ui']={IconSelect:{render:()=>null}};
mocks['@/store/modules/dict']={__esModule:true,default:()=>({removeDict(){}})};
mocks['vue-router']={useRoute:()=>({params:{dictId:dictFixtureId}})};
for(const file of ['./selector/ProtocolTypeSelector.vue','./templates/EthernetProtocolTemplate.vue','./templates/RS422ProtocolTemplate.vue','./templates/CANProtocolTemplate.vue','./templates/Protocol1553BTemplate.vue','./ImportFileDialog.vue'])mocks[file]={__esModule:true,default:{render:()=>null}};
let dictFixtureId;
async function inventory(){return {menu:await menus.listMenu(),post:await posts.listPost({page:1,pageSize:10000}),notice:await notices.listNotice({page:1,pageSize:10000}),project:await projects.listProject({page:1,pageSize:10000}),protocol:await protocols.listProtocol({page:1,pageSize:10000}),dict:await dicts.listType({page:1,pageSize:10000}),data:await dataApi.listData({page:1,pageSize:10000}),user:await users.listUser({page:1,pageSize:10000})};}
(async()=>{
 const owned=Object.fromEntries(['menu','post','notice','project','protocol','data','user'].map(k=>[k,[]]));let dictionary;
 await new Promise(resolve=>gateway.listen(0,'127.0.0.1',resolve));const gatewayBase='http://127.0.0.1:'+gateway.address().port;
 interceptor=http.axiosInstance.interceptors.request.use(config=>{
  if(config.method==='get'&&targetUrl(config.url)){
   if(invalidPrefix&&new RegExp('^'+invalidPrefix+'\\d+$').test(config.url)){config.url=invalidPrefix+'2147483646';invalidPrefix=undefined;}
   if(viaGateway)config.baseURL=gatewayBase;
   reads.push({url:config.url,signal:config.signal});
  }
  return config;
 });
 try{
  const captcha=await login.getCodeImg(),session=await login.login('admin','admin123','',captcha.uuid);auth.setToken(session.token);auth.setCsrfToken(session.csrfToken||'');loggedIn=true;assert.equal((await login.getInfo()).user.userName,'admin');
  initial=await inventory();fs.writeFileSync(dir+'/initial-inventory.json',JSON.stringify(initial));
  dictionary=await dicts.addType({dictName:tag,dictType:tag,status:'0'});dictFixtureId=dictionary.dictId;
  for(let i=0;i<2;i++){
   owned.menu.push(await menus.addMenu({parentId:0,menuName:tag+i,menuType:'F',orderNum:i,isFrame:'1',isCache:'0',visible:'1',status:'0',path:'',perms:tag+':'+i}));
   owned.post.push(await posts.addPost({postCode:tag+i,postName:tag+i,postSort:i,status:'0',remark:tag}));
   owned.notice.push(await notices.addNotice({noticeTitle:tag+i,noticeType:'1',noticeContent:'<p>'+tag+i+'</p>',status:'0'}));
   owned.project.push(await projects.addProject({projectName:tag+i,projectDesc:tag+i}));
   owned.protocol.push(await protocols.addProtocol({protocolName:tag+i,protocolType:'can',description:tag,protocolConfig:{fields:[]}}));
   owned.data.push(await dataApi.addData({dictType:tag,dictLabel:tag+i,dictValue:String(i),dictSort:i,status:'0',listClass:'default',remark:tag}));
   await users.addUser({userName:tag+i,nickName:tag+i,password:'admin123',status:'0',postIds:[],roleIds:[],remark:tag});
   owned.user.push((await users.listUser({userName:tag+i,page:1,pageSize:100})).items.find(r=>r.userName===tag+i));
  }
  const variants=[
   {kind:'menu',path:'views/system/menu/components/MenuDrawer.vue',key:'menu',id:'menuId',field:'menuName',prefix:'/system/menu/',count:2,read:menus.getMenu,arg:id=>id?{menuId:id}:undefined},
   {kind:'notice',path:'views/system/notice/components/NoticeDlg.vue',key:'notice',id:'noticeId',field:'noticeTitle',prefix:'/system/notice/',count:1,read:notices.getNotice,arg:id=>id},
   {kind:'post',path:'views/system/post/components/PostDlg.vue',key:'post',id:'postId',field:'postName',prefix:'/system/post/',count:1,read:posts.getPost,arg:id=>id},
   {kind:'system-project',path:'views/system/project/components/ProjectDlg.vue',key:'project',id:'projectId',field:'projectDesc',prefix:'/project/',count:1,read:systemProjects.getProject,arg:id=>id},
   {kind:'project',path:'views/project/components/ProjectFormDialog.vue',key:'project',id:'projectId',field:'projectName',prefix:'/project/',count:1,read:projects.getProject,arg:id=>id},
   {kind:'protocol',path:'components/business/Protocol/ProtocolFormDrawer.vue',key:'protocol',id:'protocolId',field:'protocolName',prefix:'/system/protocol/',count:1,read:protocols.getProtocol,arg:id=>id?{protocolId:id}:undefined},
   {kind:'data',path:'views/system/dict/data.vue',key:'data',id:'dictCode',field:'dictLabel',prefix:'/system/dict/data/',count:1,read:dataApi.getData,arg:id=>id?{dictCode:id}:undefined},
   {kind:'user',path:'views/system/user/components/UserFormDialog.vue',key:'user',id:'userId',field:'nickName',prefix:'/system/user/',count:1,read:users.getUser,arg:id=>id},
  ];
  const record=(v,response)=>v.kind==='user'?response.data:response;
  for(const v of variants){
   const a=owned[v.key][0][v.id],b=owned[v.key][1][v.id];assert.ok(a&&b,JSON.stringify({kind:v.kind,fixtures:owned[v.key]}));const p=page(v.path,v.kind);await delay(20);const beforeA=await v.read(a);v.page=p;v.a=a;
   await check(v.kind+'-real-switch-and-save-latest',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(v.arg(a)));assert.equal(p.state.visible,true);assert.equal(p.loading,true);assert.equal(p.disabled,true);assert.equal(await p.confirm(),false);
    await until(()=>held.length===start+v.count);const signals=reads.slice(-v.count).map(r=>r.signal);const current=p.exposed.open(v.arg(b));await until(()=>held.length===start+v.count*2);assert.ok(signals.every(s=>s.aborted));
    held.slice(start+v.count,start+v.count*2).forEach(r=>r.release());await current;held.slice(start,start+v.count).forEach(r=>r.release());assert.ok(isAbortError((await old).error));viaGateway=false;
    assert.equal(p.state.data[v.id],b);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);const changed=tag+'saved'+v.kind;p.state.data[v.field]=changed;assert.notEqual(await p.confirm(),false);
    assert.equal(record(v,await v.read(b))[v.field],changed);assert.deepEqual(await v.read(a),beforeA);
    if(v.kind==='protocol')assert.deepEqual(p.state.data.protocolConfig,{fields:[]});if(v.kind==='notice')assert.equal(p.state.data.noticeContent,'<p>'+tag+'1</p>');if(v.kind==='user')assert.deepEqual(p.state.data.roleIds,[]);
    return {upstreamStatuses:held.slice(start,start+v.count*2).map(r=>r.status),oldXhrCancelled:true,onlySelectedRecordSaved:true,placeholderSaveBlocked:true};
   });
   await check(v.kind+'-same-id-close-reopen',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(v.arg(a)));await until(()=>held.length===start+v.count);await p.exposed.close();assert.equal(p.state.visible,false);const current=p.exposed.open(v.arg(a));await until(()=>held.length===start+v.count*2);held.slice(start,start+v.count).forEach(r=>r.release());await old;await delay(10);assert.equal(p.loading,true);assert.equal(p.disabled,true);held.slice(start+v.count,start+v.count*2).forEach(r=>r.release());await current;viaGateway=false;assert.equal(p.state.data[v.id],a);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);return {sameId:true,oldFinallyPreservesLoading:true};
   });
   await check(v.kind+'-edit-to-create',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(v.arg(a)));await until(()=>held.length===start+v.count);viaGateway=false;await p.exposed.open(v.arg());held.slice(start,start+v.count).forEach(r=>r.release());await old;assert.equal(p.state.data[v.id]??null,null);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);
    if(v.kind==='menu'){assert.equal(p.state.data.parentId,0);assert.equal(p.b.menuOptions.value[0].id,0);assert.ok(p.b.menuOptions.value[0].children.length);await p.exposed.open({parentId:a});assert.equal(p.state.data.parentId,a);}
    if(v.kind==='data')assert.equal(p.state.data.dictType,tag);if(v.kind==='user'){assert.ok(Array.isArray(p.b.roleOptions.value));assert.ok(Array.isArray(p.b.postOptions.value));}
    return {newDraftSurvivesOldEdit:true,legalCreationOptionsPreserved:true};
   });
   await check(v.kind+'-current-404-and-retry',async()=>{
    const feedback=feedbackCalls;invalidPrefix=v.prefix;const failed=await outcome(p.exposed.open(v.arg(a)));originalError(failed.error,404);assert.equal(p.disabled,true);assert.equal(await p.confirm(),false);assert.equal(feedbackCalls,feedback+1);await p.b.handleRetry();assert.equal(p.state.data[v.id],a);assert.equal(p.disabled,false);assert.equal(p.b.loadError.value,'');return {status:404,feedbackOnce:true,failedEditBlocked:true,retryOriginalId:true};
   });
   await check(v.kind+'-unmount',async()=>{
    const other=page(v.path,v.kind);await delay(20);viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(other.exposed.open(v.arg(a)));await until(()=>held.length===start+v.count);other.dispose();assert.ok(isAbortError((await old).error));held.slice(start,start+v.count).forEach(r=>r.release());viaGateway=false;assert.equal(feedbackCalls,feedback);return {xhrCancelled:true,noLateFeedback:true};
   });
  }
  await check('real-parent-event-handlers-own-read-errors',async()=>{
   const definitions=[['views/system/menu/components/MenuList.vue','menu','menuDrawerRef'],['views/system/notice/components/NoticeList.vue','notice','noticeDlgRef'],['views/system/post/components/PostList.vue','post','postDlgRef'],['views/system/project/components/ProjectList.vue','system-project','projectDlgRef'],['views/project/index.vue','project','projectDialogRef'],['views/protocol/index.vue','protocol','protocolDrawerRef']];
   for(const [file,kind,ref] of definitions){const v=variants.find(v=>v.kind===kind);const code=fs.readFileSync(root+'/src/'+file,'utf8');let name=kind==='project'?'handleEdit':kind==='protocol'?'handleDetailPage':'handleUpdate';if(!code.includes('function '+name+'(')){console.log('parent-method-selection',file);continue;}const context={[ref]:{value:v.page.exposed},ids:{value:[v.a]}};const h=handlers(file,[name],context);const feedback=feedbackCalls;invalidPrefix=v.prefix;await h[name]({[v.id]:v.a});await until(()=>!v.page.loading&&Boolean(v.page.b.loadError.value));assert.equal(feedbackCalls,feedback+1);assert.equal(v.page.disabled,true);}
   const v=variants.find(v=>v.kind==='data'),feedback=feedbackCalls;invalidPrefix=v.prefix;await v.page.b.handleUpdate({dictCode:v.a});assert.equal(feedbackCalls,feedback+1);assert.equal(v.page.disabled,true);return {productionHandlers:7,parentErrorsConsumed:true};
  });
  await check('user-current-401-recovery-and-retry',async()=>{
   const v=variants.find(v=>v.kind==='user'),token=auth.getToken(),feedback=feedbackCalls;window.history.pushState({},'','/system/user');auth.setToken('invalid-remaining-editor-probe');try{const failed=await outcome(v.page.exposed.open(v.a));originalError(failed.error,401);await delay(0);assert.equal(isRelogin.show,true);assert.equal(feedbackCalls,feedback+1);assert.equal(v.page.disabled,true);assert.equal(failed.error.config.silentError,true);}finally{auth.setToken(token);dismissReloginPrompt();}await v.page.b.handleRetry();assert.equal(v.page.disabled,false);return {status:401,reloginActionOnce:true,retryOriginalUser:true};
  });
 }catch(error){console.error('PROBE_FAILURE',error.stack);throw error;}finally{
  viaGateway=false;invalidPrefix=undefined;held.forEach(r=>r.release());pages.forEach(p=>p.dispose());if(interceptor!==undefined)http.axiosInstance.interceptors.request.eject(interceptor);
  if(loggedIn){
   for(const row of owned.user)await users.delUser(row.userId);
   for(const row of owned.data)await dataApi.delData(row.dictCode);
   if(dictionary)await dicts.delType(dictionary.dictId);
   for(const row of owned.protocol)await protocols.delProtocol(row.protocolId);
   for(const row of owned.project)await projects.delProject(row.projectId);
   for(const row of owned.notice)await notices.delNotice(row.noticeId);
   for(const row of owned.post)await posts.delPost(row.postId);
   for(const row of owned.menu)await menus.delMenu(row.menuId);
   const final=await inventory();if(initial)assert.deepEqual(final,initial);results.push({name:'cleanup',ok:true,allTemporaryRecordsRemoved:true,originalBusinessListsExact:true});await login.logout();auth.removeToken();
  }
  await new Promise(resolve=>gateway.close(resolve));boundMessage();boundNotification();dismissReloginPrompt();dom.window.close();
 }
 await delay(20);assert.deepEqual(unhandled,[]);fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,mode,checks:results.length,unhandledRejections:unhandled.length,evidence:'Production SFC setup/open/confirm with source ZXUI and HTTP, real Axios XHR/FastAPI/MySQL. Gateway holds real upstream responses. Native form/template rendering and visual UI not covered; no computer use.',results},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
