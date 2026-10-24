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
const dir='/tmp/ruoyi-detail-contract',tag='erd'+Date.now().toString(36),pages=[],held=[],reads=[],results=[];
const outcome=task=>task.then(value=>({value}),error=>({error}));
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(predicate){const end=Date.now()+12000;while(!predicate()){if(Date.now()>end)throw Error('Timed out waiting for upstream response');await delay(5);}}
async function check(name,fn){const result={name,ok:true,...await fn()};results.push(result);console.log(JSON.stringify(result));}
function page(componentPath,kind){
 const descriptor=parse(fs.readFileSync(root+'/src/'+componentPath,'utf8')).descriptor;
 const script=compileScript(descriptor,{id:'actual-editor-'+kind}).content;
 const output=ts.transpileModule(script,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;
 const mod={exports:{}};vm.runInThisContext('(function(require,module,exports){'+output+'\n})',{filename:componentPath})(load,mod,mod.exports);
 const component=mod.exports.default,setup=component.setup;let bindings;
 component.setup=(props,context)=>{bindings=setup(props,context);return bindings;};component.render=()=>null;
 const events=[],app=vue.createApp(component,{save:async data=>protocolSaves.push(data),onSuccess:()=>events.push('success'),onConfirm:()=>events.push('confirm')});app.config.globalProperties.handleTree=load('@/utils/ruoyi').handleTree;
 const host=document.createElement('div');document.body.append(host);const exposed=app.mount(host);let disposed=false;
 let checked=[];const tree={getCheckedKeys:()=>checked,getHalfCheckedKeys:()=>[],setCheckedKeys:keys=>{checked=[...keys];},setChecked:id=>{checked.push(id);}};
 if(kind==='role')bindings.menuRef.value=tree;if(kind==='scope')bindings.deptRef.value=tree;
 const p={exposed,events,tree,get b(){return bindings;},get state(){return bindings.drawer?.state||bindings.state;},get props(){return bindings.drawer?bindings.drawer.drawerProps.value:bindings.dialogProps.value;},get loading(){return (bindings.drawerLoading||bindings.detailLoading).value;},get disabled(){return p.props.okDisabled||Boolean(bindings.loadError.value);},dispose(){if(!disposed){app.unmount();host.remove();disposed=true;}}};pages.push(p);return p;
}
let viaGateway=false,invalidPrefix,interceptor,loggedIn=false,initial;
const targetUrl=url=>/^\/system\/(?:config\/\d+|dict\/type\/\d+|dept\/(?:\d+|list(?:\/exclude\/\d+)?)|role\/(?:\d+|deptTree\/\d+)|menu\/(?:treeselect|roleMenuTreeselect\/\d+))$/.test(url||'');
const gateway=createServer(async(incoming,res)=>{
 res.setHeader('Access-Control-Allow-Origin','http://127.0.0.1:8088');res.setHeader('Access-Control-Allow-Credentials','true');res.setHeader('Access-Control-Allow-Headers','Authorization, X-CSRF-Token, Content-Type');res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');
 if(incoming.method==='OPTIONS'){res.writeHead(204);res.end();return;}
 try{const upstream=await fetch('http://127.0.0.1:8088'+incoming.url,{headers:{Authorization:incoming.headers.authorization||''}});const bytes=Buffer.from(await upstream.arrayBuffer());res.statusCode=upstream.status;for(const key of ['content-type','x-request-id'])if(upstream.headers.get(key))res.setHeader(key,upstream.headers.get(key));held.push({url:incoming.url,status:upstream.status,release(){if(!res.destroyed&&!res.writableEnded)res.end(bytes);}});}catch(error){if(!res.destroyed){res.statusCode=502;res.end('{}');}}
});
async function inventory(){return {config:await configs.listConfig({page:1,pageSize:10000}),dict:await dicts.listType({page:1,pageSize:10000}),dept:await depts.listDept(),role:await roles.listRole({page:1,pageSize:10000})};}
function flatten(nodes){return nodes.flatMap(node=>[node,...flatten(node.children||[])]);}
function originalError(error,status){assert.ok(error instanceof HttpError, 'Expected HttpError: '+String(error));assert.equal(error.status,status);assert.equal(error.problem.status,status);assert.equal(error.cause.config,error.config);assert.equal(error.cause.response,error.response);}
function handlers(file,names,context){const descriptor=parse(fs.readFileSync(root+'/src/'+file,'utf8')).descriptor;const ast=ts.createSourceFile(file+'.ts',descriptor.scriptSetup.content,ts.ScriptTarget.Latest,true,ts.ScriptKind.TS);const source=ast.statements.filter(n=>ts.isFunctionDeclaration(n)&&names.includes(n.name?.text)).map(n=>n.getText(ast)).join('\n');const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;return vm.runInNewContext(code+'\n({'+names.join(',')+'})',context);}
const extra={
 data:load('@/api/system/dict/data'),post:load('@/api/system/post'),notice:load('@/api/system/notice'),
 project:load('@/api/project/project'),systemProject:load('@/api/system/project'),version:load('@/api/project/version'),
 protocol:load('@/api/protocol/protocol'),job:load('@/api/monitor/job'),gen:load('@/api/tool/gen'),
 device:load('@/api/device/device'),category:load('@/api/device/category'),user:load('@/api/system/user'),
};
const {DetailIdentityError}=load('@/api/detail');
const protocolSaves=[];
for(const file of ['./selector/ProtocolTypeSelector.vue','./templates/EthernetProtocolTemplate.vue','./templates/RS422ProtocolTemplate.vue','./templates/CANProtocolTemplate.vue','./templates/Protocol1553BTemplate.vue','./ImportFileDialog.vue'])mocks[file]={__esModule:true,default:{render:()=>null}};
const feedbackCount=()=>feedbackCalls+messages.length;
const mutations=[];let forbidMutations=false,requestInterceptor,responseInterceptor,corrupt;
const knownId=2147483646;
const detailReads=[
 ['config',configs.getConfig],['dict-type',dicts.getType],['dict-data',extra.data.getData],['dept',depts.getDept],['role',roles.getRole],['menu',menus.getMenu],['post',extra.post.getPost],['notice',extra.notice.getNotice],['project',extra.project.getProject],['system-project',extra.systemProject.getProject],['version',extra.version.getProjectVersion],['protocol',extra.protocol.getProtocol],['job',extra.job.getJob],['generator',extra.gen.getGenTable],['device',extra.device.getDevice],['category',extra.category.getDeviceCategory],['user',extra.user.getUser],
];
function injectOwnedCache(namespace,id,field,action='inject'){
 const code=`import os,sys,json,hashlib,redis\nfrom dotenv import dotenv_values\ncfg=dotenv_values('.env.dev')\nr=redis.Redis(host=cfg.get('REDIS_HOST','127.0.0.1'),port=int(cfg.get('REDIS_PORT','6379')),db=int(cfg.get('REDIS_DATABASE',cfg.get('REDIS_DB','2'))),password=cfg.get('REDIS_PASSWORD') or None)\nns,identity,field=sys.argv[1],int(sys.argv[2]),sys.argv[3]\nparts={ns+'_id':identity}\nkey='query_cache:'+ns+':detail:'+hashlib.md5(json.dumps(parts,sort_keys=True,default=str).encode()).hexdigest()\nif sys.argv[4]=='inject': r.setex(key,60,json.dumps({field:None}))\nprint(json.dumps({'injectedOwnInvalidCache':ns,'keyExists':bool(r.exists(key)),'actualId':json.loads(r.get(key) or '{}').get(field)}))`;
 const result=require('node:child_process').spawnSync(root+'/../ruoyi-fastapi-backend/venv/bin/python',['-c',code,namespace,String(id),field,action],{cwd:root+'/../ruoyi-fastapi-backend',encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);assert.ok(JSON.parse(result.stdout).keyExists);if(action==='check')assert.equal(JSON.parse(result.stdout).actualId,id);
}
(async()=>{
 let fixture,initialInventory;
 requestInterceptor=http.axiosInstance.interceptors.request.use(config=>{
  if(config.method!=='get'){
   mutations.push({method:config.method,url:config.url});
   if(forbidMutations)throw Error('Unexpected write from a failed editor');
  }
  return config;
 });
 responseInterceptor=http.axiosInstance.interceptors.response.use(response=>{
  if(corrupt&&response.config.url===corrupt.url){
   const target=corrupt.nested?response.data[corrupt.nested]:response.data;
   target[corrupt.field]=corrupt.value;
   corrupt=undefined;
  }
  return response;
 });
 try{
  const captcha=await login.getCodeImg(),session=await login.login('admin','admin123','',captcha.uuid);auth.setToken(session.token);auth.setCsrfToken(session.csrfToken||'');loggedIn=true;
  const me=await login.getInfo();assert.equal(me.user.userName,'admin');initialInventory=await inventory();
  for(const [kind,read]of detailReads)await check(kind+'-real-missing-detail-problem',async()=>{
   const failed=await outcome(read(knownId));originalError(failed.error,404);
   assert.match(failed.error.response.headers['content-type'],/application\/problem\+json/);
   assert.equal(failed.error.problem.instance.includes(String(knownId)),true);
   assert.ok(failed.error.problem.errorCode);
   return {status:404,problemDetails:true,originalCauseAndConfig:true};
  });
  await check('real-user-creation-options-and-empty-collections',async()=>{
   const options=await extra.user.getUser(undefined);assert.equal(options.data,null);assert.ok(Array.isArray(options.roles));assert.ok(Array.isArray(options.posts));
   const emptyConfig=await configs.listConfig({configName:tag,page:1,pageSize:10});assert.deepEqual(emptyConfig.items,[]);assert.equal(emptyConfig.total,0);
   const emptyDict=await extra.data.getDicts(tag);assert.deepEqual(emptyDict.items,[]);
   return {creationOptionsWithoutUser:true,emptyPage:true,emptyDictionary:true};
  });
  const parent=initialInventory.dept.items.find(row=>row.parentId===0)||initialInventory.dept.items[0];
  fixture={};
  fixture.config=await configs.addConfig({configName:tag,configKey:tag,configValue:'before',configType:'N'});
  fixture.dict=await dicts.addType({dictName:tag,dictType:tag,status:'0'});
  fixture.dept=await depts.addDept({parentId:parent.deptId,deptName:tag,orderNum:0,status:'0'});
  fixture.role=await roles.addRole({roleName:tag,roleKey:tag,roleSort:0,status:'0',dataScope:'2',deptCheckStrictly:true,menuCheckStrictly:true,deptIds:[fixture.dept.deptId],menuIds:[]});
  fixture.protocol=await extra.protocol.addProtocol({protocolName:tag,protocolType:'can',protocolConfig:{},description:tag});
  for(const [namespace,id,field,read]of [['role',fixture.role.roleId,'roleId',roles.getRole],['dept',fixture.dept.deptId,'deptId',depts.getDept]])await check(namespace+'-real-old-empty-detail-cache-recovers',async()=>{
   injectOwnedCache(namespace,id,field);const data=await read(id);assert.equal(data[field],id);injectOwnedCache(namespace,id,field,'check');return {invalidOwnedCacheReplaced:true,realDatabaseIdentity:id};
  });
  const variants=[
   {kind:'config',path:'views/system/config/components/ConfigDlg.vue',field:'configId',id:fixture.config.configId,url:'/system/config/'+fixture.config.configId,arg:id=>id},
   {kind:'dict',path:'views/system/dict/components/DictDlg.vue',field:'dictId',id:fixture.dict.dictId,url:'/system/dict/type/'+fixture.dict.dictId,arg:id=>id},
   {kind:'dept',path:'views/system/dept/components/DeptDlg.vue',field:'deptId',id:fixture.dept.deptId,url:'/system/dept/'+fixture.dept.deptId,arg:id=>({deptId:id})},
   {kind:'role',path:'views/system/role/components/RoleFormDrawer.vue',field:'roleId',id:fixture.role.roleId,url:'/system/role/'+fixture.role.roleId,arg:id=>id},
   {kind:'scope',path:'views/system/role/components/RoleDataScopeDrawer.vue',field:'roleId',id:fixture.role.roleId,url:'/system/role/'+fixture.role.roleId,arg:id=>id},
   {kind:'user',path:'views/system/user/components/UserFormDialog.vue',field:'userId',id:me.user.userId,url:'/system/user/'+me.user.userId,arg:id=>id,nested:'data'},
   {kind:'protocol',path:'components/business/Protocol/ProtocolFormDrawer.vue',field:'protocolId',id:fixture.protocol.protocolId,url:'/system/protocol/'+fixture.protocol.protocolId,arg:id=>({protocolId:id})},
  ];
  for(const item of variants){
   const p=page(item.path,item.kind);item.page=p;
   for(const value of [null,knownId])await check(item.kind+'-real-200-identity-'+(value===null?'missing':'foreign'),async()=>{
    corrupt={url:item.url,field:item.field,value,nested:item.nested};const feedback=feedbackCount(),writes=mutations.length,saves=protocolSaves.length;forbidMutations=true;
    try{
     const failed=await outcome(p.exposed.open(item.arg(item.id)));assert.ok(failed.error instanceof DetailIdentityError);assert.equal(failed.error.expectedId,item.id);assert.equal(p.loading,false);
     assert.equal(await p.props.confirm(p.state.data),false);assert.equal(mutations.length,writes);assert.equal(protocolSaves.length,saves);assert.equal(feedbackCount(),feedback+1);
     return {realResponseIdentityCorruptedForFaultInjection:true,localIdentityError:true,feedbackOnce:true,writeBlocked:true};
    }finally{forbidMutations=false;corrupt=undefined;}
   });
   await check(item.kind+'-real-normal-read-recovers',async()=>{
    await p.exposed.open(item.arg(item.id));assert.equal(p.state.data[item.field],item.id);assert.equal(p.loading,false);
    if(item.kind!=='protocol')assert.equal(p.disabled,false);else assert.equal(p.props.okDisabled,false);
    return {requestedIdentityRetained:true,failedReadRecoverable:true};
   });
  }
  await check('config-real-edit-stays-put-and-reads-back-same-id',async()=>{
   const p=variants[0].page,writes=mutations.length;p.state.data.configValue='after';assert.notEqual(await p.props.confirm(p.state.data),false);
   assert.deepEqual(mutations.slice(writes).map(row=>row.method),['put']);const saved=await configs.getConfig(fixture.config.configId);assert.equal(saved.configId,fixture.config.configId);assert.equal(saved.configValue,'after');
   return {method:'PUT',sameIdSaved:true,realDatabaseValue:'after'};
  });
  await check('real-missing-detail-preserves-delete-batch-rollback',async()=>{
   const failed=await outcome(configs.delConfig(String(fixture.config.configId)+','+knownId));originalError(failed.error,404);
   const retained=await configs.getConfig(fixture.config.configId);assert.equal(retained.configValue,'after');
   return {status:404,firstRecordStillExists:true,transactionRolledBack:true};
  });
  await extra.protocol.delProtocol(fixture.protocol.protocolId);await roles.delRole(fixture.role.roleId);await depts.delDept(fixture.dept.deptId);await dicts.delType(fixture.dict.dictId);await configs.delConfig(fixture.config.configId);
  for(const item of variants)await check(item.kind+'-real-404-edit-cannot-become-create',async()=>{
   const id=item.kind==='user'?knownId:item.id,feedback=feedbackCount(),writes=mutations.length,saves=protocolSaves.length;forbidMutations=true;
   try{
    const failed=await outcome(item.page.exposed.open(item.arg(id)));originalError(failed.error,404);assert.equal(item.page.loading,false);assert.equal(await item.page.props.confirm(item.page.state.data),false);assert.equal(mutations.length,writes);assert.equal(protocolSaves.length,saves);assert.equal(feedbackCount(),feedback+1);
    return {status:404,editSaveBlocked:true,noPostOrPut:true,feedbackOnce:true};
   }finally{forbidMutations=false;}
  });
  await check('real-deliberate-creation-after-failed-edit-remains-available',async()=>{
   for(const item of variants.filter(item=>!['scope'].includes(item.kind))){
    await item.page.exposed.open(item.kind==='dept'?{parentId:parent.deptId}:undefined);
    assert.equal(item.page.state.data[item.field]??null,null);assert.equal(item.page.loading,false);
    if(item.kind==='protocol')assert.equal(item.page.props.okDisabled,false);else assert.equal(item.page.disabled,false);
   }
   return {creationEditors:6,deptParentRetained:true,userOptionsRetained:true};
  });
 }finally{
  forbidMutations=false;corrupt=undefined;pages.forEach(p=>p.dispose());
  if(loggedIn){
   const current=await inventory();
   const protocolPage=await extra.protocol.listProtocol({protocolName:tag,page:1,pageSize:10000});for(const row of protocolPage.items.filter(row=>row.protocolName===tag))await extra.protocol.delProtocol(row.protocolId);
   const ownedRole=current.role.items.filter(row=>row.roleKey===tag);if(ownedRole.length)await roles.delRole(ownedRole.map(row=>row.roleId).join(','));
   for(const row of current.dept.items.filter(row=>row.deptName===tag))await depts.delDept(row.deptId);
   const ownedDict=current.dict.items.filter(row=>row.dictType===tag);if(ownedDict.length)await dicts.delType(ownedDict.map(row=>row.dictId).join(','));
   const ownedConfig=current.config.items.filter(row=>row.configKey===tag);if(ownedConfig.length)await configs.delConfig(ownedConfig.map(row=>row.configId).join(','));
   const final=await inventory();if(initialInventory)assert.deepEqual(final,initialInventory);
   results.push({name:'cleanup',ok:true,originalListsAndTotalsExact:true,originalCounts:Object.fromEntries(Object.entries(final).map(([key,value])=>[key,value.items.length]))});
   await login.logout();auth.removeToken();
  }
  http.axiosInstance.interceptors.request.eject(requestInterceptor);http.axiosInstance.interceptors.response.eject(responseInterceptor);boundMessage();boundNotification();dismissReloginPrompt();dom.window.close();
 }
 await delay(20);assert.deepEqual(unhandled,[]);
 fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,mode,checks:results.length,unhandledRejections:unhandled.length,evidence:'Production API/HTTP and seven editor setup/open/confirm paths with source ZXUI hooks, real Axios XHR/FastAPI/MySQL. Invalid 200 cases corrupt only the ID of real responses. Native forms/tree/visuals not rendered; no computer use.',results},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
