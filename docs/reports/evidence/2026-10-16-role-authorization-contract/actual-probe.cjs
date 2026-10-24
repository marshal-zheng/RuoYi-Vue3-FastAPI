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
const depts=load('@/api/system/dept'),roles=load('@/api/system/role'),menus=load('@/api/system/menu'),users=load('@/api/system/user'),posts=load('@/api/system/post');
const {HttpError,isAbortError}=load('@zxio/http');
const unhandled=[];process.on('unhandledRejection',error=>unhandled.push(String(error)));
let feedbackCalls=0;
const boundMessage=load('@/utils/feedback/message').bindMessageFeedback(()=>{feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const boundNotification=load('@/utils/feedback/notification').bindNotificationFeedback(()=>{feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const request=load('@/utils/request').default;
const dir='/tmp/ruoyi-role-authorization',tag='rac'+Date.now().toString(36),results=[],pages=[];
const outcome=p=>p.then(value=>({value}),error=>({error}));
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const writes=[];let interceptor,initial,adminSession,actorSession;
const owned={role:[],post:[],dept:[],user:[]};
function useSession(session){auth.setToken(session.token);auth.setCsrfToken(session.csrfToken||'');dismissReloginPrompt();}
async function signIn(userName,password='admin123'){const captcha=await login.getCodeImg();return login.login(userName,password,'',captcha.uuid);}
async function check(name,action){const value={name,ok:true,...await action()};results.push(value);console.log(JSON.stringify(value));}
async function inventory(){return {user:await users.listUser({page:1,pageSize:10000}),role:await roles.listRole({page:1,pageSize:10000}),post:await posts.listPost({page:1,pageSize:10000}),dept:await depts.listDept()};}
async function userState(id){const r=await users.getUser(id);return {user:r.data,roles:[...(r.roleIds||[])].sort(),posts:[...(r.postIds||[])].sort()};}
async function roleState(id){return {role:await roles.getRole(id),menus:[...(await menus.roleMenuTreeselect(id)).checkedKeys].sort(),depts:[...(await roles.deptTreeSelect(id)).checkedKeys].sort()};}
function expectProblem(error,status,field){assert.ok(error instanceof HttpError,String(error));assert.equal(error.status,status);assert.equal(error.problem.status,status);assert.match(error.response.headers['content-type'],/application\/problem\+json/);assert.equal(error.cause.config,error.config);if(field)assert.ok(error.problem.errors.some(row=>row.field===field||row.field.startsWith(field+'.')),JSON.stringify(error.problem.errors));}
let currentRoute={params:{}};
function page(file,props={}){
 const source=fs.readFileSync(root+'/src/'+file,'utf8');const descriptor=parse(source).descriptor;
 const script=compileScript(descriptor,{id:'authorization-probe'}).content;
 const output=ts.transpileModule(script,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;const mod={exports:{}};
 const localRequire=id=>id.endsWith('.vue')?{__esModule:true,default:{render:()=>null}}:load(id);
 vm.runInThisContext('(function(require,module,exports,useRoute){const {ref,reactive,getCurrentInstance,nextTick}=require("vue");'+output+'\n})',{filename:file})(localRequire,mod,mod.exports,()=>currentRoute);
 const component=mod.exports.default,setup=component.setup;let b;component.setup=(props,ctx)=>{b=setup(props,ctx);return b;};component.render=()=>null;
 const app=vue.createApp(component,props),host=document.createElement('div');document.body.append(host);
 app.config.globalProperties.$tab={closeOpenPage(){}};app.config.globalProperties.useDict=()=>({sys_normal_disable:vue.ref([])});app.config.globalProperties.$modal={confirm:()=>Promise.resolve()};app.mount(host);
 const p={b,dispose(){app.unmount();host.remove();}};pages.push(p);return p;
}
const probeConfig=JSON.parse(fs.readFileSync(dir+'/config.json','utf8'));
const sessions=[];
const diagnostic=async()=> (await axios.get('http://127.0.0.1:8088/__authorization_probe',{headers:{'x-probe-secret':probeConfig.secret}})).data;
const raw=(url,data,config={})=>request({url,method:'put',data,feedback:{mode:'auto'},...config});
async function failure(name,action,status){
 const before=(await diagnostic()).relations;const feedbackBefore=feedbackCalls;
 const result=await outcome(action());expectProblem(result.error,status);
 assert.equal(feedbackCalls-feedbackBefore,1,name+' single feedback');assert.equal(isRelogin.show,false,name+' no relogin');
 assert.deepEqual((await diagnostic()).relations,before,name+' unchanged associations');
 assert.ok(result.error.config.url);assert.ok(['put','post'].includes(result.error.config.method));
 results.push({name,ok:true,status,serverRequestId:!!(result.error.problem.requestId||result.error.response.headers['x-request-id']),singleFeedback:true,unchangedRelations:true,noRelogin:true});console.log(JSON.stringify(results.at(-1)));
}
async function signInWithCaptcha(userName,password='admin123'){
 const captcha=await login.getCodeImg();let code='';
 if(captcha.captchaEnabled){const {execFileSync}=require('node:child_process');code=execFileSync('redis-cli',['-p','16379','-n','2','GET','captcha_codes:'+captcha.uuid],{encoding:'utf8'}).trim();}
 const session=await login.login(userName,password,code,captcha.uuid);sessions.push(session);return session;
}
(async()=>{
 let originalRelations;
 function remember(kind,row){owned[kind].push(row);fs.writeFileSync(dir+'/owned.json',JSON.stringify({tag,owned}));return row;}
 try{
  interceptor=http.axiosInstance.interceptors.request.use(async config=>{await delay(650);return config;});
  adminSession=await signInWithCaptcha('admin');useSession(adminSession);initial=await inventory();originalRelations=(await diagnostic()).relations;
  fs.writeFileSync(dir+'/initial-inventory.json',JSON.stringify(initial));fs.writeFileSync(dir+'/initial-relations.json',JSON.stringify(originalRelations));
  const parent=initial.dept.items.find(d=>d.parentId===0)||initial.dept.items[0];assert.ok(parent);
  const menuRows=(await menus.listMenu()).items;const perms=['system:user:edit','system:user:query','system:user:list','system:user:add','system:role:edit','system:role:list'];
  const menuIds=perms.map(perm=>{const row=menuRows.find(r=>r.perms===perm);assert.ok(row,perm);return row.menuId;});
  for(let i=0;i<2;i++)remember('dept',await depts.addDept({parentId:parent.deptId,deptName:tag+'d'+i,orderNum:i,status:'0'}));
  for(let i=0;i<6;i++)remember('role',await roles.addRole({roleName:tag+'r'+i,roleKey:tag+'r'+i,roleSort:i,status:'0',menuIds:i===3||i===4?menuIds:[]}));
  const [rA,rB,rKeep,rScope,rAll,rNo]=owned.role.map(r=>r.roleId);const [dIn,dOut]=owned.dept.map(d=>d.deptId);
  await roles.dataScope({roleId:rScope,dataScope:'3',deptIds:[]});
  const defs=[[dIn,[rA,rKeep]],[dIn,[rKeep]],[dOut,[rB]],[dIn,[rScope]],[dIn,[rAll]],[dIn,[rNo]]];
  for(let i=0;i<defs.length;i++){const created=await users.addUser({userName:tag+'u'+i,nickName:tag+'u'+i,password:'admin123',deptId:defs[i][0],status:'0',roleIds:defs[i][1]});remember('user',created.data||created);}
  const [u1,u2,uOut,actorScoped,actorGlobal,actorNo]=owned.user.map(u=>u.userId);
  const allSession=await signInWithCaptcha(owned.user[4].userName),scopedSession=await signInWithCaptcha(owned.user[3].userName),noSession=await signInWithCaptcha(owned.user[5].userName);useSession(adminSession);
  const rels=async id=>(await diagnostic()).relations.filter(r=>r[0]===id).map(r=>r[1]).sort((a,b)=>a-b);
  const target=owned.user.slice(0,3).map(u=>u.userId);
  const endpoints=[['/system/user/authRole',{userId:u1,roleIds:[rA,rKeep]}],['/system/role/authUser/selectAll',{roleId:rA,userIds:[u2]}],['/system/role/authUser/cancel',{roleId:rA,userId:u1}],['/system/role/authUser/cancelAll',{roleId:rA,userIds:[u1,u2]}]];
  for(const [url,payload] of endpoints){
   const wrong=url.endsWith('/authRole')?{roleId:rB,userIds:[u2]}:url.endsWith('/cancel')?{userIds:[u2]}:{userId:u1,roleIds:[rB]};
   await failure('reject-pollution-'+url,()=>raw(url,{...payload,...wrong}),422);
   const idKey=url.endsWith('/authRole')?'userId':'roleId';
   for(const bad of [0,-1,true,'42',1.5,null])await failure('reject-id-'+url+'-'+String(bad),()=>raw(url,{...payload,[idKey]:bad}),422);
   const required=url.endsWith('/authRole')?'roleIds':url.endsWith('/cancel')?'userId':'userIds';
   const omitted={...payload};delete omitted[required];await failure('reject-missing-'+url,()=>raw(url,omitted),422);
  }
  for(const [url,payload] of [endpoints[0],endpoints[1],endpoints[3]]){
   const field=url.endsWith('/authRole')?'roleIds':'userIds';
   for(const bad of [null,'1,2',[0],[true]])await failure('reject-collection-'+url+'-'+JSON.stringify(bad),()=>raw(url,{...payload,[field]:bad}),422);
   if(field==='userIds')await failure('reject-empty-'+url,()=>raw(url,{...payload,userIds:[]}),422);
  }
  await failure('old-query-only-fails',()=>raw('/system/role/authUser/selectAll',undefined,{params:{roleId:rA,userIds:String(u2),userId:u2}}),422);
  for(const [url,payload] of [
   ['/system/user/authRole',{userId:2147483647,roleIds:[]}],
   ['/system/user/authRole',{userId:u1,roleIds:[rA,2147483647]}],
   ['/system/role/authUser/selectAll',{roleId:rA,userIds:[u2,2147483647]}],
   ['/system/role/authUser/selectAll',{roleId:2147483647,userIds:[u2]}],
   ['/system/role/authUser/cancel',{roleId:rA,userId:2147483647}],
   ['/system/role/authUser/cancelAll',{roleId:rA,userIds:[u1,2147483647]}],
  ])await failure('missing-party-'+url+'-'+JSON.stringify(payload),()=>raw(url,payload),404);
  for(const [url,payload] of [
   ['/system/user/authRole',{userId:1,roleIds:[]}],
   ['/system/role/authUser/selectAll',{roleId:rA,userIds:[u2,1]}],
   ['/system/role/authUser/cancel',{roleId:rA,userId:1}],
   ['/system/role/authUser/cancelAll',{roleId:rA,userIds:[u1,1]}],
  ])await failure('protect-admin-user-'+url,()=>raw(url,payload),403);
  useSession(scopedSession);
  for(const [url,payload] of [
   ['/system/user/authRole',{userId:uOut,roleIds:[rA]}],
   ['/system/user/authRole',{userId:u1,roleIds:[rA,rB]}],
   ['/system/role/authUser/selectAll',{roleId:rA,userIds:[u2,uOut]}],
   ['/system/role/authUser/selectAll',{roleId:rB,userIds:[u2]}],
   ['/system/role/authUser/cancel',{roleId:rA,userId:uOut}],
   ['/system/role/authUser/cancel',{roleId:rB,userId:u1}],
   ['/system/role/authUser/cancelAll',{roleId:rA,userIds:[u1,uOut]}],
   ['/system/role/authUser/cancelAll',{roleId:rB,userIds:[u1]}],
  ])await failure('scope-denial-'+url+'-'+JSON.stringify(payload),()=>raw(url,payload),403);
  await check('scoped-actor-valid-grant-and-revoke',async()=>{await roles.authUserSelectAll({roleId:rA,userIds:[u2,u2]});assert.deepEqual(await rels(u2),[rA,rKeep].sort((a,b)=>a-b));await roles.authUserCancel({roleId:rA,userId:u2});assert.deepEqual(await rels(u2),[rKeep]);return {bothScopes:true};});
  useSession(allSession);
  for(const [url,payload] of [
   ['/system/user/authRole',{userId:u1,roleIds:[1]}],
   ['/system/role/authUser/selectAll',{roleId:1,userIds:[u2]}],
   ['/system/role/authUser/cancel',{roleId:1,userId:u1}],
   ['/system/role/authUser/cancelAll',{roleId:1,userIds:[u1,u2]}],
   ['/system/user',{userId:u1,roleIds:[1]}],
  ])await failure('all-scope-cannot-operate-role1-'+url,()=>raw(url,payload),403);
  await failure('create-user-cannot-assign-role1',()=>request({url:'/system/user',method:'post',data:{userName:tag+'forbidden',nickName:'Forbidden',password:'admin123',roleIds:[1],deptId:dIn},feedback:{mode:'auto'}}),403);
  useSession(noSession);for(const [url,payload] of endpoints)await failure('operation-permission-denied-'+url,()=>raw(url,payload),403);
  useSession(adminSession);
  await check('admin-can-grant-role1-to-normal-user',async()=>{await roles.authUserSelectAll({roleId:1,userIds:[u2]});assert.deepEqual(await rels(u2),[1,rKeep]);return {allowed:true};});
  useSession(allSession);await failure('empty-replacement-cannot-remove-protected-role',()=>users.updateAuthRole({userId:u2,roleIds:[]}),403);await failure('ordinary-user-editor-cannot-clear-protected-role',()=>users.updateUser({userId:u2,roleIds:null}),403);
  useSession(adminSession);await roles.authUserCancel({roleId:1,userId:u2});assert.deepEqual(await rels(u2),[rKeep]);
  await check('replacement-deduplicates-and-empty-clears',async()=>{await users.updateAuthRole({userId:u1,roleIds:[rA,rA,rKeep]});assert.deepEqual(await rels(u1),[rA,rKeep].sort((a,b)=>a-b));await users.updateAuthRole({userId:u1,roleIds:[]});assert.deepEqual(await rels(u1),[]);await users.updateAuthRole({userId:u1,roleIds:[rA,rKeep]});return {deduplicated:true,clear:true};});
  await check('incremental-and-revoke-preserve-other-associations',async()=>{await roles.authUserSelectAll({roleId:rA,userIds:[u1,u2,u2]});assert.deepEqual(await rels(u2),[rA,rKeep].sort((a,b)=>a-b));await roles.authUserCancel({roleId:rA,userId:u2});assert.deepEqual(await rels(u2),[rKeep]);await roles.authUserCancelAll({roleId:rA,userIds:[u1,u2,u2]});assert.deepEqual(await rels(u1),[rKeep]);assert.deepEqual(await rels(uOut),[rB]);return {incremental:true,idempotent:true};});
  await failure('second-insert-rolls-back-batch',()=>raw('/system/role/authUser/selectAll',{roleId:rB,userIds:[u1,u2]},{headers:{'x-probe-secret':probeConfig.secret,'x-authorization-fault':'second-insert'}}),500);
  await failure('commit-failure-rolls-back-batch',()=>raw('/system/role/authUser/selectAll',{roleId:rB,userIds:[u1,u2]},{headers:{'x-probe-secret':probeConfig.secret,'x-authorization-fault':'commit'}}),500);
  await check('production-user-role-page-load-save-and-clear',async()=>{currentRoute={params:{userId:String(u1)}};const p=page('views/system/user/authRole.vue');for(let i=0;i<100&&!p.b.rolesLoaded.value;i++)await delay(30);assert.equal(p.b.form.value.userId,u1,'actual authRole read must succeed');p.b.handleSelectionChange([{roleId:rKeep}]);await p.b.handleSave();assert.deepEqual(await rels(u1),[rKeep]);p.b.handleSelectionChange([]);await p.b.handleSave();assert.deepEqual(await rels(u1),[]);return {productionSetup:true,emptyArray:true};});
  await check('production-role-user-selector-and-revocation',async()=>{currentRoute={params:{roleId:String(rA)}};const p=page('views/system/role/selectUser.vue',{roleId:String(rA)});p.b.show();await delay(80);p.b.handleSelectionChange([{userId:u1},{userId:u2}]);await p.b.handleSelectUser();assert.deepEqual(await rels(u1),[rA]);assert.deepEqual(await rels(u2),[rA,rKeep].sort((a,b)=>a-b));const a=page('views/system/role/authUser.vue');await a.b.cancelAuthUser({userId:u1,userName:owned.user[0].userName});assert.deepEqual(await rels(u1),[]);a.b.handleSelectionChange([{userId:u2}]);await a.b.cancelAuthUserAll();assert.deepEqual(await rels(u2),[rKeep]);return {productionSetup:true,routeConvertedToNumber:true};});
 } catch(error) {console.error('PRIMARY FAILURE:',error.message);throw error;} finally {
  for(const p of pages)p.dispose();
  if(adminSession){for(const session of sessions.filter(s=>s!==adminSession)){useSession(session);await axios.post('http://127.0.0.1:8088/auth/logout',null,{headers:{Authorization:'Bearer '+auth.getToken()},adapter:'http'});}useSession(adminSession);for(const row of owned.user)await users.delUser(row.userId);for(const row of owned.role)await roles.delRole(row.roleId);for(const row of owned.dept)await depts.delDept(row.deptId);const final=await inventory();assert.deepEqual(final,initial);assert.deepEqual((await diagnostic()).relations,originalRelations);results.push({name:'cleanup',ok:true,temporaryRecordsRemoved:true,originalBusinessListsAndTotalsExact:true,originalRelationsExact:true});await axios.post('http://127.0.0.1:8088/auth/logout',null,{headers:{Authorization:'Bearer '+auth.getToken()},adapter:'http'});auth.removeToken();}
  if(interceptor!==undefined)http.axiosInstance.interceptors.request.eject(interceptor);boundMessage();boundNotification();dismissReloginPrompt();dom.window.close();
 }
 await delay(30);assert.deepEqual(unhandled,[]);fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,checks:results.length,mode,unhandledRejections:0,evidence:'Production SFC setup/actions, API/request/feedback, source ZXUI HTTP, Axios XHR, FastAPI, local MySQL and isolated Redis; no computer use or visual/native form verification.',results},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{fs.writeFileSync(dir+'/failed.json',JSON.stringify({message:error.message,results},null,2));console.error(error.message);process.exitCode=1;});
