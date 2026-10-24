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
const dir='/tmp/ruoyi-user-role-write-contract',tag='uwc'+Date.now().toString(36),results=[],pages=[];
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
 vm.runInThisContext('(function(require,module,exports){const {ref,watch,getCurrentInstance}=require("vue");'+output+'\n})',{filename:file})(load,mod,mod.exports);
 const component=mod.exports.default,setup=component.setup;let b;component.setup=(props,context)=>{b=setup(props,context);return b;};component.render=()=>null;
 const app=vue.createApp(component,props),host=document.createElement('div');document.body.append(host);app.mount(host);let checked=[];
 const tree={getCheckedKeys:()=>checked,getHalfCheckedKeys:()=>[],setCheckedKeys:ids=>{checked=[...ids];},setChecked:id=>{checked.push(id);}};
 if(kind==='role')b.menuRef.value=tree;if(kind==='scope')b.deptRef.value=tree;
 if(kind==='profile')app._instance.refs={userRef:{validate:async()=>true}};
 const p={b,tree,get state(){return b.drawer?.state||b.state;},open:id=>kind==='user'?b.openDialog(id):b.openDrawer(id),confirm:()=>kind==='profile'?b.submit():b.drawer?b.drawer.drawerProps.value.confirm(b.drawer.state.data):b.dialogProps.value.confirm(b.state.data),dispose(){app.unmount();host.remove();}};
 pages.push(p);return p;
}
(async()=>{
 try{
  adminSession=await signIn('admin');useSession(adminSession);initial=await inventory();fs.writeFileSync(dir+'/initial-inventory.json',JSON.stringify(initial));
  interceptor=http.axiosInstance.interceptors.request.use(async config=>{if(['post','put','patch','delete'].includes(config.method)){await delay(650);writes.push({method:config.method,url:config.url,data:config.data});}return config;});
  const parent=initial.dept.items.find(d=>d.parentId===0)||initial.dept.items[0];assert.ok(parent);
  const leaves=[];const walk=nodes=>nodes.forEach(n=>n.children?.length?walk(n.children):leaves.push(n.id));walk((await menus.treeselect()).items);assert.ok(leaves.length>=2);
  for(let i=0;i<2;i++){
   owned.dept.push(await depts.addDept({parentId:parent.deptId,deptName:tag+i,orderNum:i,status:'0'}));
   owned.post.push(await posts.addPost({postName:tag+i,postCode:tag+i,postSort:i,status:'0'}));
   owned.role.push(await roles.addRole({roleName:tag+i,roleKey:tag+i,roleSort:i,status:'0',menuIds:[leaves[i]],menuCheckStrictly:true}));
   await roles.dataScope({roleId:owned.role[i].roleId,dataScope:'2',deptIds:[owned.dept[i].deptId],deptCheckStrictly:true});
   const created=await users.addUser({userName:tag+i,nickName:tag+i,password:'admin123',deptId:owned.dept[i].deptId,status:'0',roleIds:[owned.role[i].roleId],postIds:[owned.post[i].postId]});
   const row=created?.data||created;assert.ok(row.userId,'Creation response must contain the created identity');owned.user.push(row);
  }
  const uid=owned.user[0].userId,otherId=owned.user[1].userId,rid=owned.role[0].roleId,did=owned.dept[0].deptId,did2=owned.dept[1].deptId,pid=owned.post[0].postId,rid2=owned.role[1].roleId;
  const unchangedOther=await userState(otherId);
  await check('user-partial-edit-preserves-omitted-relations',async()=>{const before=await userState(uid);await users.updateUser({userId:uid,nickName:tag+'edited'});const after=await userState(uid);assert.equal(after.user.nickName,tag+'edited');assert.equal(after.user.userName,before.user.userName);assert.deepEqual(after.roles,before.roles);assert.deepEqual(after.posts,before.posts);return {normalEdit:true,rolesPreserved:true,postsPreserved:true};});
  await check('user-relations-replace-empty-null-and-independent-presence',async()=>{
   await users.updateUser({userId:uid,roleIds:[rid2]});let s=await userState(uid);assert.deepEqual(s.roles,[rid2]);assert.deepEqual(s.posts,[pid]);
   await users.updateUser({userId:uid,roleIds:[]});s=await userState(uid);assert.deepEqual(s.roles,[]);assert.deepEqual(s.posts,[pid]);
   await users.updateUser({userId:uid,roleIds:[rid],postIds:[pid]});await users.updateUser({userId:uid,roleIds:null,postIds:null});s=await userState(uid);assert.deepEqual(s.roles,[]);assert.deepEqual(s.posts,[]);
   await users.updateUser({userId:uid,roleIds:[rid],postIds:[pid]});return {replace:true,emptyClears:true,nullClears:true,independentPresence:true};
  });
  await check('role-normal-edit-preserves-menus-and-data-scope',async()=>{const before=await roleState(rid);await roles.updateRole({roleId:rid,roleName:tag+'edit'});const after=await roleState(rid);assert.equal(after.role.roleName,tag+'edit');assert.deepEqual(after.menus,before.menus);assert.deepEqual(after.depts,before.depts);assert.equal(after.role.dataScope,'2');return {partialEdit:true,omittedMenusPreserved:true,dataScopeUnchanged:true};});
  await check('role-menu-replace-empty-null',async()=>{await roles.updateRole({roleId:rid,menuIds:[leaves[1]]});assert.deepEqual((await roleState(rid)).menus,[leaves[1]]);await roles.updateRole({roleId:rid,menuIds:[]});assert.deepEqual((await roleState(rid)).menus,[]);await roles.updateRole({roleId:rid,menuIds:null});assert.deepEqual((await roleState(rid)).menus,[]);await roles.updateRole({roleId:rid,menuIds:[leaves[0]]});assert.deepEqual((await roleState(rid)).depts,[did]);return {replace:true,emptyClears:true,nullClears:true,departmentsUntouched:true};});
  await check('data-scope-omitted-replace-empty-null',async()=>{await roles.dataScope({roleId:rid,dataScope:'2'});assert.deepEqual((await roleState(rid)).depts,[did]);await roles.dataScope({roleId:rid,dataScope:'2',deptIds:[did2]});assert.deepEqual((await roleState(rid)).depts,[did2]);await roles.dataScope({roleId:rid,dataScope:'2',deptIds:[]});assert.deepEqual((await roleState(rid)).depts,[]);await roles.dataScope({roleId:rid,dataScope:'2',deptIds:[did]});await roles.dataScope({roleId:rid,dataScope:'2',deptIds:null});assert.deepEqual((await roleState(rid)).depts,[]);await roles.dataScope({roleId:rid,dataScope:'2',deptIds:[did]});const menusBefore=(await roleState(rid)).menus;await roles.dataScope({roleId:rid,dataScope:'1'});const after=await roleState(rid);assert.deepEqual(after.depts,[did]);assert.deepEqual(after.menus,menusBefore);await roles.dataScope({roleId:rid,dataScope:'2'});return {omittedPreserves:true,replace:true,emptyClears:true,nullClears:true,scopeChangeWithoutDepartmentsPreserves:true};});
  await check('user-and-role-status-touch-only-status',async()=>{
   const ub=await userState(uid),rb=await roleState(rid);
   await users.changeUserStatus(uid,'1');const ua=await userState(uid);assert.equal(ua.user.status,'1');
   for(const key of ['nickName','userName','deptId','remark'])assert.deepEqual(ua.user[key],ub.user[key]);assert.deepEqual(ua.roles,ub.roles);assert.deepEqual(ua.posts,ub.posts);
   await users.changeUserStatus(uid,'0');await roles.changeRoleStatus(rid,'1');const ra=await roleState(rid);assert.equal(ra.role.status,'1');
   for(const key of ['roleName','roleKey','roleSort','dataScope'])assert.deepEqual(ra.role[key],rb.role[key]);assert.deepEqual(ra.menus,rb.menus);assert.deepEqual(ra.depts,rb.depts);
   await roles.changeRoleStatus(rid,'0');assert.deepEqual((await userState(uid)).roles,ub.roles);
   return {statusSaved:true,disabledRoleReadableAndReenableable:true,otherFieldsAndPersistedRelationsUnchanged:true};
  });
  const matrix=[
   ['profile','/system/user/profile','put',{nickName:'Rejected'},['userId','userName','deptId','status','delFlag','password','avatar','roleIds','postIds','type','createBy']],
   ['user-create','/system/user','post',{userName:tag+'reject',nickName:tag,password:'admin123'},['userId','delFlag','loginIp','avatar','type','createBy']],
   ['user-edit','/system/user','put',{userId:uid,nickName:'Rejected'},['password','avatar','delFlag','loginIp','createBy','type','admin']],
   ['user-status','/system/user/changeStatus','put',{userId:uid,status:'1'},['nickName','deptId','roleIds','postIds','password','type','createBy']],
   ['role-create','/system/role','post',{roleName:tag+'reject',roleKey:tag+'reject',roleSort:1},['roleId','dataScope','deptIds','delFlag','type','createBy']],
   ['role-edit','/system/role','put',{roleId:rid,roleName:'Rejected'},['dataScope','deptIds','delFlag','createBy','type','admin']],
   ['role-status','/system/role/changeStatus','put',{roleId:rid,status:'1'},['roleName','menuIds','dataScope','deptIds','type','createBy']],
   ['role-scope','/system/role/dataScope','put',{roleId:rid,dataScope:'2'},['roleName','roleKey','menuIds','status','type','createBy']],
  ];
  const beforeForbiddenUser=await userState(uid),beforeForbiddenRole=await roleState(rid);
  for(const [kind,url,method,data,fields] of matrix)await check(kind+'-rejects-out-of-operation-fields',async()=>{for(const field of fields){const feedback=feedbackCalls;const failed=await outcome(request({url,method,data:{...data,[field]:null},feedback:{mode:'auto'}}));expectProblem(failed.error,422,field);assert.equal(feedbackCalls,feedback+1);}return {status:422,rejectedFields:fields,problemDetails:true,feedbackOnceEach:true};});
  assert.deepEqual(await userState(uid),beforeForbiddenUser);assert.deepEqual(await roleState(rid),beforeForbiddenRole);
  await check('missing-null-and-invalid-required-fields-return-422',async()=>{
   const tests=[['/system/user',{nickName:'No ID'},'userId'],['/system/user',{userId:null},'userId'],['/system/user',{userId:uid,nickName:null},'nickName'],['/system/user/changeStatus',{userId:uid},'status'],['/system/user/changeStatus',{userId:uid,status:'9'},'status'],['/system/role',{roleName:'No ID'},'roleId'],['/system/role',{roleId:rid,roleName:null},'roleName'],['/system/role/changeStatus',{roleId:rid,status:null},'status'],['/system/role/dataScope',{roleId:rid},'dataScope'],['/system/role/dataScope',{roleId:rid,dataScope:'9'},'dataScope']];
   for(const [url,data,field]of tests){const failed=await outcome(request({url,method:'put',data}));expectProblem(failed.error,422,field);}
   const missingNickname=await outcome(request({url:'/system/user',method:'post',data:{userName:tag+'reject',password:'admin123'}}));expectProblem(missingNickname.error,422,'nickName');return {invalidRequests:tests.length+1,noDatabaseFailure:true};
  });
  await check('existing-domain-validation-remains-422-not-500',async()=>{
   for(const [url,method,data]of [
    ['/system/user','post',{userName:tag+'invalid',nickName:tag,password:'admin123',email:'not-an-email'}],
    ['/system/user','put',{userId:uid,email:'not-an-email'}],
    ['/system/user/profile','put',{email:'not-an-email'}],
    ['/system/role','post',{roleName:'',roleKey:tag+'invalid',roleSort:1}],
    ['/system/role','put',{roleId:rid,roleName:''}],
   ]){const feedback=feedbackCalls;const failed=await outcome(request({url,method,data,feedback:{mode:'auto'}}));expectProblem(failed.error,422);assert.equal(feedbackCalls,feedback+1);}return {invalidRequests:5,problemDetails:true,noAuditWrapperSystemError:true};
  });
  await check('user-form-saves-only-editor-fields-through-real-api',async()=>{const p=page('views/system/user/components/UserFormDialog.vue','user');await p.open(uid);Object.assign(p.state.data,{nickName:tag+'form',createBy:'must-not-write',loginIp:'must-not-write',password:'must-not-write',type:'status'});const before=writes.length;await p.confirm();const sent=writes.slice(before).find(w=>w.url==='/system/user'&&w.method==='put').data;for(const field of ['createBy','loginIp','password','type'])assert.ok(!(field in sent));assert.equal((await userState(uid)).user.nickName,tag+'form');return {productionComponent:true,realPut:true,displayMetadataExcluded:true};});
  await check('role-form-and-scope-drawer-use-exact-inputs',async()=>{const p=page('views/system/role/components/RoleFormDrawer.vue','role');await p.open(rid);Object.assign(p.state.data,{roleName:tag+'formrole',dataScope:'5',createBy:'must-not-write',type:'status'});await p.confirm();assert.equal((await roleState(rid)).role.roleName,tag+'formrole');assert.equal((await roleState(rid)).role.dataScope,'2');const scope=page('views/system/role/components/RoleDataScopeDrawer.vue','scope');await scope.open(rid);scope.state.data.dataScope='2';scope.tree.setCheckedKeys([did2]);const before=writes.length;await scope.confirm();const sent=writes.slice(before).find(w=>w.url==='/system/role/dataScope').data;assert.deepEqual(Object.keys(sent).sort(),['dataScope','deptCheckStrictly','deptIds','roleId']);assert.deepEqual((await roleState(rid)).depts,[did2]);return {productionComponents:2,realPuts:true,noDisplayFields:true};});
  actorSession=await signIn(owned.user[0].userName);useSession(actorSession);assert.equal((await login.getInfo()).user.userId,uid);const profile=await users.getUserProfile();assert.ok(profile.data.loginDate);
  useSession(adminSession);await users.updateUser({userId:uid,roleIds:[rid2],postIds:[owned.post[1].postId]});useSession(actorSession);
  await check('profile-saves-only-own-fields-without-replaying-login-relations',async()=>{const p=page('views/system/user/profile/userInfo.vue','profile',{user:profile.data});Object.assign(p.b.form.value,{nickName:tag+'profile',email:tag+'@example.com',phonenumber:'13800000000',sex:'1'});await p.confirm();useSession(adminSession);const after=await userState(uid);assert.equal(after.user.nickName,tag+'profile');assert.equal(after.user.email,tag+'@example.com');assert.deepEqual(after.roles,[rid2]);assert.deepEqual(after.posts,[owned.post[1].postId]);assert.equal(after.user.deptId,owned.dept[0].deptId);assert.equal(after.user.status,'0');useSession(actorSession);return {productionProfileForm:true,authenticatedIdentity:true,concurrentRoleAndPostAssignmentsPreserved:true,loginBookkeepingIntact:true};});
  await check('ordinary-user-profile-rejects-identity-and-privileged-fields',async()=>{for(const [field,value]of [['userId',otherId],['deptId',did2],['status','1'],['password','must-not-write'],['delFlag','2'],['roleIds',[]],['postIds',[]]]){const feedback=feedbackCalls;const failed=await outcome(users.updateUserProfile({nickName:'Rejected',[field]:value}));expectProblem(failed.error,422,field);assert.equal(feedbackCalls,feedback+1);}useSession(adminSession);assert.equal((await userState(uid)).user.nickName,tag+'profile');assert.deepEqual(await userState(otherId),unchangedOther);return {rejectedFields:7,ownRecordUnchanged:true,otherUserUnchanged:true};});
  useSession(actorSession);await login.logout();actorSession=undefined;const relogin=await signIn(owned.user[0].userName);useSession(relogin);assert.equal((await login.getInfo()).user.userId,uid);await login.logout();useSession(adminSession);
  await check('scoped-user-partial-edit-preserves-target-user-permission',async()=>{
   const menuRows=(await menus.listMenu()).items;
   const editPermission=menuRows.find(row=>row.perms==='system:user:edit');assert.ok(editPermission);
   const selfRole=await roles.addRole({roleName:tag+'self',roleKey:tag+'self',roleSort:3,status:'0',menuIds:[editPermission.menuId]});owned.role.push(selfRole);
   await roles.dataScope({roleId:selfRole.roleId,dataScope:'5',deptIds:[]});
   await users.updateUser({userId:uid,roleIds:[selfRole.roleId]});const scopedSession=await signIn(owned.user[0].userName);useSession(scopedSession);
   await users.updateUser({userId:uid,nickName:tag+'scoped'});
   const forbidden=await outcome(users.updateUser({userId:otherId,nickName:'must-not-write'}));expectProblem(forbidden.error,401);assert.equal(forbidden.error.problem.errorCode,30010);assert.match(forbidden.error.problem.detail,/没有权限访问用户数据/);
   await login.logout();useSession(adminSession);const after=await userState(uid);assert.equal(after.user.nickName,tag+'scoped');assert.deepEqual(await userState(otherId),unchangedOther);
   return {selfOnlyRole:true,omittedDepartmentDoesNotRequireUnrelatedDepartmentPermission:true,otherUserStillForbidden:true,existingDataScopeErrorCode:30010,existingDataScopeHttpStatus:401};
  });
  await check('normal-user-and-role-creation-persisted-as-intended',async()=>{const userList=await users.listUser({userName:tag,page:1,pageSize:100});assert.equal(userList.items.filter(u=>u.userName===tag+'reject').length,0);const roleList=await roles.listRole({roleKey:tag+'reject',page:1,pageSize:100});assert.equal(roleList.items.length,0);return {twoUsersAndRolesCreated:true,forbiddenCreatesProducedNoRows:true,originalPasswordStillAuthenticates:true};});
 }catch(error){console.error('PROBE_FAILURE',error.stack||error);throw error;}finally{
  pages.forEach(p=>p.dispose());if(adminSession){useSession(adminSession);for(const row of owned.user)await users.delUser(row.userId);for(const row of owned.role)await roles.delRole(row.roleId);for(const row of owned.post)await posts.delPost(row.postId);for(const row of owned.dept)await depts.delDept(row.deptId);const final=await inventory();if(initial)assert.deepEqual(final,initial);results.push({name:'cleanup',ok:true,temporaryRecordsRemoved:true,originalBusinessListsAndTotalsExact:true});await login.logout();auth.removeToken();}if(interceptor!==undefined)http.axiosInstance.interceptors.request.eject(interceptor);boundMessage();boundNotification();dismissReloginPrompt();dom.window.close();
 }
 await delay(10);assert.deepEqual(unhandled,[]);fs.writeFileSync(dir+'/actual.json',JSON.stringify({ok:true,mode,checks:results.length,unhandledRejections:0,evidence:'Production HTTP/API modules and four SFC setup/submit paths, source ZXUI, real Axios XHR/FastAPI/MySQL. No native form or visual browser rendering; no computer use.',results},null,2));console.log(JSON.stringify({ok:true,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
