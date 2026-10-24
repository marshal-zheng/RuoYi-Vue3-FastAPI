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
const dir='/tmp/ruoyi-editor-reads',tag='erd'+Date.now().toString(36),pages=[],held=[],reads=[],results=[];
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
 const events=[],app=vue.createApp(component,{onSuccess:()=>events.push('success'),onConfirm:()=>events.push('confirm')});app.config.globalProperties.handleTree=load('@/utils/ruoyi').handleTree;
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
(async()=>{
 await new Promise(resolve=>gateway.listen(0,'127.0.0.1',resolve));const gatewayBase='http://127.0.0.1:'+gateway.address().port;
 interceptor=http.axiosInstance.interceptors.request.use(config=>{
  if(config.method==='get'&&targetUrl(config.url)){
   if(invalidPrefix&&new RegExp('^'+invalidPrefix+'\\d+$').test(config.url)){config.url=invalidPrefix+'2147483646/editor-read-probe-missing';invalidPrefix=undefined;}
   if(viaGateway)config.baseURL=gatewayBase;
   reads.push({url:config.url,signal:config.signal});
  }
  return config;
 });
 try{
  const captcha=await login.getCodeImg(),session=await login.login('admin','admin123','',captcha.uuid);auth.setToken(session.token);auth.setCsrfToken(session.csrfToken||'');loggedIn=true;
  assert.equal((await login.getInfo()).user.userName,'admin');initial=await inventory();fs.writeFileSync(dir+'/initial-inventory.json',JSON.stringify(initial,null,2));
  const fixture={config:[],dict:[],dept:[],role:[]};
  const parent=initial.dept.items.find(d=>d.parentId===0)||initial.dept.items[0];assert.ok(parent);
  const menuNodes=flatten((await menus.treeselect()).items).filter(node=>!node.children?.length);assert.ok(menuNodes.length>=2);
  for(let i=0;i<2;i++){
   fixture.config.push(await configs.addConfig({configName:tag+i,configKey:tag+'.'+i,configValue:'initial',configType:'N',remark:tag}));
   fixture.dict.push(await dicts.addType({dictName:tag+i,dictType:tag+'_'+i,status:'0',remark:tag}));
   fixture.dept.push(await depts.addDept({parentId:parent.deptId,deptName:tag+i,orderNum:i,status:'0'}));
   fixture.role.push(await roles.addRole({roleName:tag+i,roleKey:tag+'_'+i,roleSort:i,status:'0',dataScope:'2',menuCheckStrictly:true,deptCheckStrictly:true,menuIds:[menuNodes[i].id],deptIds:[fixture.dept[i].deptId],remark:tag}));
  }
  const variants=[
   {kind:'config',path:'views/system/config/components/ConfigDlg.vue',id:'configId',field:'configName',prefix:'/system/config/',count:1,fixtures:fixture.config,read:configs.getConfig,arg:id=>id},
   {kind:'dict',path:'views/system/dict/components/DictDlg.vue',id:'dictId',field:'dictName',prefix:'/system/dict/type/',count:1,fixtures:fixture.dict,read:dicts.getType,arg:id=>id},
   {kind:'dept',path:'views/system/dept/components/DeptDlg.vue',id:'deptId',field:'deptName',prefix:'/system/dept/',count:2,fixtures:fixture.dept,read:depts.getDept,arg:id=>id?{deptId:id}:{parentId:parent.deptId}},
   {kind:'role',path:'views/system/role/components/RoleFormDrawer.vue',id:'roleId',field:'roleName',prefix:'/system/role/',count:2,fixtures:fixture.role,read:roles.getRole,arg:id=>id},
   {kind:'scope',path:'views/system/role/components/RoleDataScopeDrawer.vue',id:'roleId',field:'dataScope',prefix:'/system/role/',count:2,fixtures:fixture.role,read:roles.getRole,arg:id=>id},
  ];
  for(const item of variants){
   const a=item.fixtures[0][item.id],b=item.fixtures[1][item.id];assert.ok(a&&b,JSON.stringify(item.fixtures));const p=page(item.path,item.kind),beforeA=await item.read(a);
   await check(item.kind+'-real-switch-and-save-only-latest',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(item.arg(a)));
    assert.equal(p.state.visible,true);assert.equal(p.loading,true);assert.equal(p.disabled,true);assert.equal(await p.props.confirm({}),false);
    await until(()=>held.length===start+item.count);const oldSignals=reads.slice(-item.count).map(read=>read.signal);
    const current=p.exposed.open(item.arg(b));await until(()=>held.length===start+item.count*2);assert.ok(oldSignals.every(signal=>signal.aborted));
    held.slice(start+item.count,start+item.count*2).forEach(entry=>entry.release());await current;held.slice(start,start+item.count).forEach(entry=>entry.release());const failed=await old;assert.ok(isAbortError(failed.error));viaGateway=false;
    assert.equal(p.state.data[item.id],b);assert.equal(p.loading,false);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);
    const expected=tag+'saved'+item.kind;
    if(item.kind==='scope'){p.state.data.dataScope='2';p.tree.setCheckedKeys(fixture.dept.map(row=>row.deptId));}else p.state.data[item.field]=expected;
    if(item.kind==='dept')p.state.data.status='1'; // Avoid unrelated ancestor timestamp updates from the backend's normal-status propagation.
    const selected=JSON.parse(JSON.stringify(p.state.data));const saved=await p.props.confirm({});assert.notEqual(saved,false);
    const afterB=await item.read(b),afterA=await item.read(a);assert.deepEqual(afterA,beforeA);
    if(item.kind==='scope'){assert.equal(afterB.dataScope,'2');const checks=(await roles.deptTreeSelect(b)).checkedKeys;assert.deepEqual([...checks].sort(),fixture.dept.map(row=>row.deptId).sort());}
    else assert.equal(afterB[item.field],expected);
    if(item.kind==='role')assert.deepEqual((await menus.roleMenuTreeselect(b)).checkedKeys,[menuNodes[1].id]);
    return {upstreamStatuses:held.slice(start,start+item.count*2).map(row=>row.status),allOldXhrsCancelled:true,placeholderSaveBlocked:true,savedOnlyLatestId:b,otherRecordUnchanged:true,selectionMatchedSaved:afterB[item.id]===selected[item.id],treePermissionsVerified:item.kind==='role'||item.kind==='scope'};
   });
   await check(item.kind+'-real-close-reopen-keeps-current-loading',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(item.arg(a)));await until(()=>held.length===start+item.count);
    await p.exposed.close();assert.equal(p.state.visible,false);const current=p.exposed.open(item.arg(a));await until(()=>held.length===start+item.count*2);
    held.slice(start,start+item.count).forEach(entry=>entry.release());await old;await delay(10);assert.equal(p.state.visible,true);assert.equal(p.loading,true);assert.equal(p.disabled,true);
    held.slice(start+item.count,start+item.count*2).forEach(entry=>entry.release());await current;viaGateway=false;assert.equal(p.state.data[item.id],a);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);
    return {sameRecordReopened:true,oldFinallyDidNotClearLoading:true,noCancellationFeedback:true};
   });
   if(item.kind!=='scope')await check(item.kind+'-real-edit-to-create',async()=>{
    viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(p.exposed.open(item.arg(a)));await until(()=>held.length===start+item.count);viaGateway=false;
    await p.exposed.open(item.arg());held.slice(start,start+item.count).forEach(entry=>entry.release());await old;await delay(10);
    assert.equal(p.state.data[item.id],undefined);assert.equal(p.disabled,false);assert.equal(feedbackCalls,feedback);
    if(item.kind==='dept'){assert.equal(p.state.data.parentId,parent.deptId);assert.equal(p.state.data.orderNum,0);assert.equal(p.state.data.status,'0');assert.ok(p.b.deptOptions.value.length);}
    if(item.kind==='role')assert.ok(p.b.menuOptions.value.length);
    return {newDraftSurvivesOldEdit:true,realCreationOptions:item.kind==='dept'||item.kind==='role',createDefaultsRetained:true};
   });
   await check(item.kind+'-real-current-404-and-retry',async()=>{
    const feedback=feedbackCalls;invalidPrefix=item.prefix;const failed=await outcome(p.exposed.open(item.arg(a)));originalError(failed.error,404);
    assert.equal(p.loading,false);assert.equal(p.disabled,true);assert.equal(p.b.loadError.value,failed.error.message);assert.equal(await p.props.confirm({}),false);assert.equal(feedbackCalls,feedback+1);
    await p.b.handleRetry();assert.equal(p.state.data[item.id],a);assert.equal(p.disabled,false);assert.equal(p.b.loadError.value,'');assert.equal(feedbackCalls,feedback+1);
    return {status:404,originalCauseAndConfig:true,feedbackOnce:true,failedReadCannotSave:true,retrySameRecord:true};
   });
   await check(item.kind+'-real-unmount-cancels-read',async()=>{
    const other=page(item.path,item.kind);viaGateway=true;const start=held.length,feedback=feedbackCalls;const old=outcome(other.exposed.open(item.arg(a)));await until(()=>held.length===start+item.count);other.dispose();const failed=await old;assert.ok(isAbortError(failed.error));assert.equal(failed.error.reason,'editor-opening-ended');held.slice(start,start+item.count).forEach(entry=>entry.release());viaGateway=false;assert.equal(feedbackCalls,feedback);return {xhrCancelled:true,cancelReasonRetained:true,noLateFeedback:true};
   });
   item.page=p;item.a=a;
  }
  await check('real-parent-event-endpoints-own-already-presented-read-rejections',async()=>{
   const definitions=[
    {file:'views/system/config/components/ConfigList.vue',kind:'config',ref:'configDlgRef'},
    {file:'views/system/dict/components/DictList.vue',kind:'dict',ref:'dictDlgRef'},
    {file:'views/system/dept/components/DeptList.vue',kind:'dept',ref:'deptDlgRef'},
    {file:'views/system/role/index.vue',kind:'role',ref:'roleFormDrawerRef'},
   ];
   for(const def of definitions){const v=variants.find(item=>item.kind===def.kind),context={[def.ref]:{value:v.page.exposed},ids:{value:[v.a]}};const h=handlers(def.file,['handleUpdate'],context);const feedback=feedbackCalls;invalidPrefix=v.prefix;await h.handleUpdate({[v.id]:v.a});assert.equal(feedbackCalls,feedback+1);assert.equal(v.page.disabled,true);await h.handleUpdate({[v.id]:v.a});assert.equal(v.page.disabled,false);}
   return {productionHandlers:4,real404Consumed:true,noDuplicateFeedback:true,normalReopen:true};
  });
  await check('real-current-401-retains-relogin-action-and-retry',async()=>{
   const v=variants[0],token=auth.getToken(),feedback=feedbackCalls;window.history.pushState({},'','/system/config');auth.setToken('invalid-editor-probe');
   try{const failed=await outcome(v.page.exposed.open(v.arg(v.a)));originalError(failed.error,401);await delay(0);assert.equal(isRelogin.show,true);assert.equal(feedbackCalls,feedback+1);assert.equal(v.page.disabled,true);assert.equal(failed.error.config.silentError,true);}finally{auth.setToken(token);dismissReloginPrompt();}
   await v.page.b.handleRetry();assert.equal(v.page.disabled,false);return {status:401,reloginActionOnce:true,originalSilentConfigRetained:true,validSessionRetry:true};
  });
 }finally{
  viaGateway=false;invalidPrefix=undefined;held.forEach(entry=>entry.release());pages.forEach(p=>p.dispose());if(interceptor!==undefined)http.axiosInstance.interceptors.request.eject(interceptor);
  if(loggedIn){
   const finalBefore=await inventory(),owned={};
   for(const key of ['config','dict','dept','role'])owned[key]=finalBefore[key].items.filter(row=>String(row[{config:'configKey',dict:'dictType',dept:'deptName',role:'roleKey'}[key]]).startsWith(tag));
   if(owned.role.length)await roles.delRole(owned.role.map(row=>row.roleId).join(','));
   for(const row of owned.dept)await depts.delDept(row.deptId);
   if(owned.dict.length)await dicts.delType(owned.dict.map(row=>row.dictId).join(','));
   if(owned.config.length)await configs.delConfig(owned.config.map(row=>row.configId).join(','));
   const final=await inventory();fs.writeFileSync(dir+'/final-inventory.json',JSON.stringify(final,null,2));if(initial)assert.deepEqual(final,initial);
   results.push({name:'cleanup',ok:true,temporaryRowsDeleted:Object.fromEntries(Object.entries(owned).map(([key,value])=>[key,value.length])),originalCounts:Object.fromEntries(Object.entries(final).map(([key,value])=>[key,value.items.length])),originalDetailsAndTotalsUnchanged:true});
   await login.logout();auth.removeToken();
  }
  boundMessage();boundNotification();dismissReloginPrompt();gateway.closeAllConnections();await new Promise(resolve=>gateway.close(resolve));dom.window.close();
 }
 await delay(20);assert.deepEqual(unhandled,[]);
 fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,mode,evidence:'Production five editor setup/open/confirm functions + API/HTTP/feedback + source ZXUI hooks, real Axios XHR/FastAPI/MySQL, loopback proxy only holds actual responses. Native forms/tree and visuals not rendered; no computer use.',results,unhandledRejections:unhandled.length},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
