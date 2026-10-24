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
const feedbackEvents=[];let feedbackCalls=0;
const boundMessage=load('@/utils/feedback/message').bindMessageFeedback(options=>{feedbackEvents.push({channel:"message",...options});feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const boundNotification=load('@/utils/feedback/notification').bindNotificationFeedback(options=>{feedbackEvents.push({channel:"notification",...options});feedbackCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const request=load('@/utils/request').default;
const dir='/tmp/ruoyi-http-error-classification',tag='ec'+Date.now().toString(36),results=[],pages=[];
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
function page(file,kind,props={}){
 const source=fs.readFileSync(root+'/src/'+file,'utf8');const descriptor=parse(source).descriptor;
 const script=compileScript(descriptor,{id:'actual-write-'+kind}).content;const output=ts.transpileModule(script,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;const mod={exports:{}};
 vm.runInThisContext('(function(require,module,exports){const {ref,reactive,watch,getCurrentInstance}=require("vue");'+output+'\n})',{filename:file})(load,mod,mod.exports);
 const component=mod.exports.default,setup=component.setup;let b;component.setup=(props,context)=>{b=setup(props,context);return b;};component.render=()=>null;
 const app=vue.createApp(component,props),host=document.createElement('div');document.body.append(host);app.mount(host);let checked=[];
 const tree={getCheckedKeys:()=>checked,getHalfCheckedKeys:()=>[],setCheckedKeys:ids=>{checked=[...ids];},setChecked:id=>{checked.push(id);}};
 if(kind==='role')b.menuRef.value=tree;if(kind==='scope')b.deptRef.value=tree;
 if(kind==='profile')app._instance.refs={userRef:{validate:async()=>true}};if(kind==='password')app._instance.refs={pwdRef:{validate:async()=>true}};
 const p={b,tree,get state(){return b.drawer?.state||b.state;},open:id=>kind==='user'?b.openDialog(id):b.openDrawer(id),confirm:()=>['profile','password'].includes(kind)?b.submit():b.drawer?b.drawer.drawerProps.value.confirm(b.drawer.state.data):b.dialogProps.value.confirm(b.state.data),dispose(){app.unmount();host.remove();}};
 pages.push(p);return p;
}

async function expectFailure(name, action, status, code, options={}) {
 const before=feedbackEvents.length,token=auth.getToken();
 const failed=await outcome(action());expectProblem(failed.error,status);if(code!==undefined)assert.equal(failed.error.problem.errorCode,code);
 const problem=failed.error.problem;assert.ok(problem.requestId);assert.ok(problem.instance);if(options.field)assert.ok(problem.errors.some(row=>row.field===options.field));
 await delay(20);const feedback=feedbackEvents.slice(before),relogin=feedback.filter(row=>row.message==='登录状态已失效');
 assert.equal(feedback.length,options.feedbackCount??1,name+' feedback count');assert.equal(relogin.length,status===401?1:0,name+' relogin count');
 if(status===401)assert.equal(isRelogin.show,true);else{assert.equal(isRelogin.show,false);assert.equal(auth.getToken(),token);}
 results.push({name,ok:true,status,errorCode:problem.errorCode,problemDetails:true,errorContextPreserved:true,feedbackCount:feedback.length,reloginCount:relogin.length,...(options.field?{validationField:options.field}:{})});
 console.log(JSON.stringify(results.at(-1)));return failed.error;
}
(async()=>{
 try{
  adminSession=await signIn('admin');useSession(adminSession);initial=await inventory();fs.writeFileSync(dir+'/initial-inventory.json',JSON.stringify(initial));
  interceptor=http.axiosInstance.interceptors.request.use(async config=>{if(['post','put','patch','delete'].includes(config.method)){await delay(650);writes.push({method:config.method,url:config.url,data:config.data});}return config;});
  const menuRows=(await menus.listMenu()).items;const permissions=['system:user:query','system:user:edit','system:user:remove','system:user:resetPwd'];const permissionIds=permissions.map(perm=>{const row=menuRows.find(row=>row.perms===perm);assert.ok(row,perm);return row.menuId;});
  const selfRole=await roles.addRole({roleName:tag+'self',roleKey:tag+'self',roleSort:9,status:'0',menuIds:permissionIds});owned.role.push(selfRole);await roles.dataScope({roleId:selfRole.roleId,dataScope:'5',deptIds:[]});
  for(let i=0;i<2;i++){const created=await users.addUser({userName:tag+i,nickName:tag+i,password:'admin123',status:'0',roleIds:i===0?[selfRole.roleId]:[],postIds:[]});const row=created?.data||created;assert.ok(row.userId);owned.user.push(row);}
  const actor=owned.user[0],other=owned.user[1],otherBefore=await userState(other.userId),adminBefore=await userState(1);
  actorSession=await signIn(actor.userName);useSession(actorSession);assert.equal((await login.getInfo()).user.userId,actor.userId);
  await check('allowed-self-edit-and-profile-still-work',async()=>{await users.updateUser({userId:actor.userId,nickName:tag+'allowed'});assert.equal((await users.getUserProfile()).data.nickName,tag+'allowed');return {realPartialEdit:true,sessionValid:true};});
  for(const [name,action]of [
   ['out-of-scope-detail',()=>users.getUser(other.userId)],
   ['out-of-scope-edit',()=>users.updateUser({userId:other.userId,nickName:'must-not-write'})],
   ['out-of-scope-status',()=>users.changeUserStatus(other.userId,'1')],
   ['out-of-scope-delete',()=>users.delUser(other.userId)],
   ['out-of-scope-reset-password',()=>users.resetUserPwd(other.userId,'must-not-write')],
  ])await expectFailure(name,action,403,30010,{feedbackCount:name.endsWith('reset-password')?0:1});
  for(const [name,action]of [
   ['protected-admin-edit',()=>users.updateUser({userId:1,nickName:'must-not-write'})],
   ['protected-admin-status',()=>users.changeUserStatus(1,'1')],
   ['protected-admin-delete',()=>users.delUser(1)],
   ['protected-admin-reset-password',()=>users.resetUserPwd(1,'must-not-write')],
  ])await expectFailure(name,action,403,30009,{feedbackCount:name.endsWith('reset-password')?0:1});
  await check('denied-writes-preserve-records-and-live-session',async()=>{assert.equal((await users.getUserProfile()).data.userId,actor.userId);useSession(adminSession);assert.deepEqual(await userState(other.userId),otherBefore);assert.deepEqual(await userState(1),adminBefore);useSession(actorSession);return {otherUserAndAdminUnchanged:true,actorSessionStillValid:true};});
  for(const field of ['oldPassword','newPassword'])for(const value of ['missing',null,'']){const data={oldPassword:'admin123',newPassword:'Changed123!'};if(value==='missing')delete data[field];else data[field]=value;await expectFailure('profile-password-rejects-'+field+'-'+String(value),()=>request({url:'/system/user/profile/updatePwd',method:'put',data,feedback:{mode:'auto'}}),422,undefined,{field});}
  const pwd=page('views/system/user/profile/resetPwd.vue','password');Object.assign(pwd.b.user,{oldPassword:'Incorrect123!',newPassword:'Changed123!',confirmPassword:'Changed123!'});
  const beforePasswordWrites=writes.length;
  await expectFailure('profile-form-wrong-old-password',()=>pwd.confirm(),422,30011,{field:'oldPassword'});
  assert.equal(pwd.b.submitPending.value,false);assert.equal(writes.slice(beforePasswordWrites).filter(row=>row.url==='/system/user/profile/updatePwd').length,1);
  await check('wrong-password-preserves-session-and-allows-form-correction',async()=>{
   assert.equal((await users.getUserProfile()).data.userId,actor.userId);actorSession=await signIn(actor.userName);useSession(actorSession);
   pwd.b.user.oldPassword='admin123';await pwd.confirm();assert.equal(pwd.b.submitPending.value,false);
   const changed=await signIn(actor.userName,'Changed123!');useSession(changed);assert.equal((await login.getInfo()).user.userId,actor.userId);await login.logout();useSession(actorSession);
   return {productionPasswordForm:true,wrongPasswordDidNotChangeCredential:true,correctedSubmissionSucceeded:true,newPasswordAuthenticated:true,pendingReleased:true};
  });
  // A role-less authenticated account still receives a normal 403 at the interface guard.
  const noPermission=await signIn(other.userName);useSession(noPermission);
  await expectFailure('missing-interface-permission',()=>users.getUser(actor.userId),403,20004);
  assert.equal((await users.getUserProfile()).data.userId,other.userId);await login.logout();useSession(adminSession);
  // Isolate the harness cookie jar so the missing-token request cannot use a login cookie.
  auth.removeToken();dom.cookieJar.removeAllCookiesSync();dismissReloginPrompt();
  await expectFailure('missing-authentication',()=>users.getUserProfile(),401);
  useSession({token:'not-a-valid-token'});await expectFailure('invalid-authentication',()=>users.getUserProfile(),401);
  const disposable=await signIn(other.userName);useSession(disposable);await login.logout();useSession(disposable);
  await expectFailure('revoked-session',()=>users.getUserProfile(),401);
  useSession(adminSession);await check('valid-session-recovers-after-real-401',async()=>{assert.equal((await login.getInfo()).user.userId,1);assert.equal(isRelogin.show,false);return {realAuthenticatedRead:true,reloginPromptDismissed:true};});
 }finally{
  pages.forEach(p=>p.dispose());if(adminSession){useSession(adminSession);for(const row of owned.user)await users.delUser(row.userId);for(const row of owned.role)await roles.delRole(row.roleId);const final=await inventory();assert.deepEqual(final,initial);results.push({name:'cleanup',ok:true,temporaryRecordsRemoved:true,originalBusinessListsAndTotalsExact:true});await login.logout();auth.removeToken();}if(interceptor!==undefined)http.axiosInstance.interceptors.request.eject(interceptor);boundMessage();boundNotification();dismissReloginPrompt();dom.window.close();
 }
 await delay(10);assert.deepEqual(unhandled,[]);fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,mode,checks:results.length,unhandledRejections:0,evidence:'Production HTTP/API, production password-form setup/submit, source ZXUI, real Axios XHR/FastAPI/MySQL. Native validation and visual UI were not rendered. No computer use.',results},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
