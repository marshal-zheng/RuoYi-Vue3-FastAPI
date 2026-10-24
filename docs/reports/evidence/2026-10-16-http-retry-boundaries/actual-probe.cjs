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


// Production HTTP, API, feedback, operation and download modules; only UI delivery is stubbed.
delete mocks['@/utils/feedback/presenter'];
delete mocks['@/utils/feedback/message'];
const {http,isRelogin,dismissReloginPrompt}=load('@/utils/http');
const auth=load('@/utils/auth'),login=load('@/api/login'),configs=load('@/api/system/config');
const {download,downloadFile}=load('@/utils/request');
const {useOperation}=load('@/utils/operation');
const {createHttpClient,HttpError,AbortError}=load('@zxio/http');
let messageCalls=0,notificationCalls=0;
const unbindMessage=load('@/utils/feedback/message').bindMessageFeedback(()=>{messageCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const unbindNotification=load('@/utils/feedback/notification').bindNotificationFeedback(()=>{notificationCalls++;return Promise.resolve({ok:true,value:{close(){}}});});
const results=[],counts=new Map(),rules=[];
const dir='/tmp/ruoyi-http-retry',tag='retry'+Date.now().toString(36);
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const outcome=promise=>promise.then(value=>({value}),error=>({error}));
const seen=(method,path)=>counts.get(method+' '+path)||0;
const notices=()=>messageCalls+notificationCalls;
const feedback={mode:'auto'};
function inject(method,path,remaining,phase='before',status=503){rules.push({method,path,remaining,phase,status});}
async function check(name,fn){const result={name,ok:true,...await fn()};results.push(result);console.log(JSON.stringify(result));}
function cors(req,res){res.setHeader('Access-Control-Allow-Origin','http://127.0.0.1:8088');res.setHeader('Access-Control-Allow-Credentials','true');res.setHeader('Access-Control-Allow-Headers',req.headers['access-control-request-headers']||'*');res.setHeader('Access-Control-Allow-Methods','GET,POST,PUT,PATCH,DELETE,OPTIONS');}
function fail(res,status){res.writeHead(status,{'Content-Type':'application/problem+json'});res.end(JSON.stringify({type:'about:blank',title:'Injected transport failure',status,detail:'retry boundary probe'}));}
const proxy=createServer((req,res)=>{
 cors(req,res);if(req.method==='OPTIONS'){res.writeHead(204);res.end();return;}
 const pathname=new URL(req.url,'http://localhost').pathname,key=req.method+' '+pathname;
 counts.set(key,seen(req.method,pathname)+1);
 const rule=rules.find(r=>r.method===req.method&&r.path===pathname&&r.remaining>0);
 if(rule)rule.remaining--;
 if(rule?.phase==='before'){req.resume();fail(res,rule.status);return;}
 const upstream=nodeRequest({hostname:'127.0.0.1',port:8088,path:req.url,method:req.method,headers:{...req.headers,host:'127.0.0.1:8088'}},response=>{
  const parts=[];response.on('data',part=>parts.push(part));response.on('end',()=>{
   if(rule?.phase==='after'){assert.ok(response.statusCode>=200&&response.statusCode<300);fail(res,rule.status);return;}
   const headers={...response.headers};delete headers['access-control-allow-origin'];delete headers['access-control-allow-credentials'];
   res.writeHead(response.statusCode,headers);res.end(Buffer.concat(parts));
  });
 });upstream.on('error',()=>{if(!res.headersSent)fail(res,502);else res.end();});req.pipe(upstream);
});
let initial,loggedIn=false;
function originalError(error,status){assert.ok(error instanceof HttpError);assert.equal(error.status,status);assert.equal(error.cause.config,error.config);assert.equal(error.cause.response,error.response);assert.equal(error.problem.status,status);}
(async()=>{
 await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));
 const proxyUrl='http://127.0.0.1:'+proxy.address().port;
 http.config.axiosConfig.baseURL=proxyUrl;http.axiosInstance.defaults.baseURL=proxyUrl;
 try{
  await check('real-login-and-business-default-retry-off',async()=>{
   assert.equal(http.config.retry,undefined);
   const captcha=await login.getCodeImg();
   const session=await login.login('admin','admin123','',captcha.uuid);
   auth.setToken(session.token);auth.setCsrfToken(session.csrfToken||'');loggedIn=true;
   assert.equal((await login.getInfo()).user.userName,'admin');
   initial=await configs.listConfig({page:1,pageSize:10000});assert.equal(initial.items.length,7);assert.equal(initial.total,7);
   return {authenticated:true,globalRetryConfigured:false,existingConfigs:initial.items.length};
  });
  await check('real-business-read-failure-is-not-automatically-retried',async()=>{
   const n=seen('GET','/system/config/list');inject('GET','/system/config/list',1);
   const failed=await outcome(configs.listConfig({page:1,pageSize:10}));originalError(failed.error,503);
   assert.equal(seen('GET','/system/config/list')-n,1);
   return {attempts:1,status:503,problemCauseAndConfigPreserved:true};
  });
  await check('real-read-recovers-without-intermediate-business-feedback',async()=>{
   const n=seen('GET','/system/config/list'),before=notices();inject('GET','/system/config/list',1);
   const result=await http.get({url:'/system/config/list',params:{pager:{page:1,size:10}},feedback},{retry:{count:2,delay:5}});
   assert.equal(seen('GET','/system/config/list')-n,2);assert.equal(notices(),before);assert.equal(result.items.length,7);assert.equal(result.pager.total,7);
   return {attempts:2,errorFeedback:0,realFastApiListAndPager:true};
  });
  await check('real-business-error-hook-enhances-only-the-final-failure',async()=>{
   const n=seen('GET','/system/config/list'),before=notices();inject('GET','/system/config/list',3);
   const failed=await outcome(http.get({url:'/system/config/list',feedback},{retry:{count:2,delay:1}}));originalError(failed.error,503);
   assert.equal(seen('GET','/system/config/list')-n,3);assert.equal(notices()-before,1);
   return {attempts:3,errorFeedback:1,originalAxiosAndEnhancedProblemRetained:true};
  });
  await check('committed-real-write-response-failure-is-not-replayed-by-business',async()=>{
   const n=seen('POST','/system/config'),before=notices();inject('POST','/system/config',1,'after');
   const operation=useOperation(()=>configs.addConfig({configName:tag,configKey:tag+'.business',configValue:'once',configType:'N',remark:tag}));
   const task=operation.run();assert.equal(operation.pending.value,true);const failed=await outcome(task);originalError(failed.error,503);
   assert.equal(operation.pending.value,false);assert.equal(seen('POST','/system/config')-n,1);assert.equal(notices()-before,1);
   assert.equal((await configs.getConfigKey(tag+'.business')).configValue,'once');
   return {forwardedAndCommittedWrites:1,automaticReplays:0,errorFeedback:1,pendingReleased:true,readbackVerified:true};
  });
  await check('enabled-library-retry-still-does-not-replay-a-committed-write',async()=>{
   const n=seen('POST','/system/config');inject('POST','/system/config',1,'after');
   const client=createHttpClient({...http.config,retry:{count:2,delay:0}});
   const failed=await outcome(client.post({url:'/system/config',data:{configName:tag,configKey:tag+'.library',configValue:'once',configType:'N',remark:tag}}));originalError(failed.error,503);
   assert.equal(seen('POST','/system/config')-n,1);assert.equal((await configs.getConfigKey(tag+'.library')).configValue,'once');
   return {configuredRetryCount:2,forwardedAndCommittedWrites:1,automaticReplays:0,readbackVerified:true};
  });
  await check('real-409-conflict-retains-cause-context-and-business-detail',async()=>{
   const n=seen('POST','/system/config');const failed=await outcome(configs.addConfig({configName:tag,configKey:tag+'.business',configValue:'duplicate',configType:'N'}));originalError(failed.error,409);
   assert.equal(seen('POST','/system/config')-n,1);assert.equal((await configs.getConfigKey(tag+'.business')).configValue,'once');
   return {attempts:1,status:409,originalCauseAndEnhancedProblem:true,existingValueUnchanged:true};
  });
  await check('backoff-cancel-releases-real-business-operation-immediately',async()=>{
   const controller=new AbortController(),reason=Object.freeze({owner:'retry-probe'}),before=notices(),n=seen('GET','/system/config/list');inject('GET','/system/config/list',1);
   let waitingResolve;const waiting=new Promise(resolve=>{waitingResolve=resolve;});
   const operation=useOperation(()=>http.get({url:'/system/config/list',signal:controller.signal,feedback},{retry:{count:2,delay:()=>{waitingResolve();return 1000;}}}));
   const task=outcome(operation.run());assert.equal(operation.pending.value,true);await waiting;const start=performance.now();controller.abort(reason);const failed=await task;const elapsed=performance.now()-start;
   assert.ok(failed.error instanceof AbortError);assert.equal(failed.error.reason,reason);assert.equal(failed.error.cause.status,503);assert.equal(failed.error.cause.cause.config,failed.error.config);assert.equal(operation.pending.value,false);assert.equal(seen('GET','/system/config/list')-n,1);assert.equal(notices(),before);assert.ok(elapsed<150);
   return {backoffMs:1000,cancelElapsedMs:Number(elapsed.toFixed(2)),attempts:1,cancelReasonLastAxiosErrorAndConfig:true,errorFeedback:0,pendingReleased:true};
  });
  await check('real-response-transform-and-resolver-exceptions-preserve-identity',async()=>{
   for(const stage of ['afterResponse','successResolver']){
    const n=seen('GET','/getInfo'),original=Object.freeze(new Error(stage+' failure'));
    const extra=stage==='afterResponse'?{transforms:[...http.config.transforms,{afterResponse(){throw original;}}]}:{successResolver(){throw original;}};
    const client=createHttpClient({...http.config,...extra,retry:{count:2,delay:0,retryCondition:()=>true}});
    const failed=await outcome(client.get({url:'/getInfo'}));assert.equal(failed.error,original);assert.equal(seen('GET','/getInfo')-n,1);
   }
   return {realFastApiResponses:2,transportAttemptsPerSemanticFailure:1,exceptionIdentity:true};
  });
  await check('real-axios-response-transform-is-outside-retry',async()=>{
   const original=Object.freeze(new Error('Axios response transform failure')),n=seen('GET','/getInfo');
   const client=createHttpClient({...http.config,axiosConfig:{...http.config.axiosConfig,transformResponse:[()=>{throw original;}]},retry:{count:2,delay:0,retryCondition:()=>true}});
   const failed=await outcome(client.get({url:'/getInfo'}));assert.equal(failed.error,original);assert.equal(seen('GET','/getInfo')-n,1);
   return {realFastApiResponse:true,attempts:1,axiosTransformExceptionIdentity:true};
  });
  await check('real-401-auth-hook-runs-once-and-keeps-its-exception',async()=>{
   const n=seen('GET','/system/config/list'),original=Object.freeze(new Error('auth hook failure'));let calls=0;
   const client=createHttpClient({axiosConfig:http.config.axiosConfig,successResolver:http.config.successResolver,tokenProvider:{getToken:()=> 'retry-invalid-token',onAuthError(){calls++;throw original;}},retry:{count:1,delay:0,retryCondition:()=>true}});
   const failed=await outcome(client.get({url:'/system/config/list'}));assert.equal(failed.error,original);assert.equal(calls,1);assert.equal(seen('GET','/system/config/list')-n,2);
   return {real401Attempts:2,finalAuthHookCalls:1,authExceptionIdentity:true};
  });
  await check('real-business-401-prompts-once-after-final-attempt',async()=>{
   const token=auth.getToken(),n=seen('GET','/system/config/list'),before=messageCalls;window.history.pushState({},'','/system/config');auth.setToken('retry-invalid-token');
   try{const failed=await outcome(http.get({url:'/system/config/list'},{retry:{count:1,delay:0,retryCondition:()=>true}}));originalError(failed.error,401);await delay(0);assert.equal(messageCalls-before,1);assert.equal(isRelogin.show,true);assert.equal(seen('GET','/system/config/list')-n,2);}finally{dismissReloginPrompt();auth.setToken(token);}
   assert.equal((await login.getInfo()).user.userName,'admin');return {real401Attempts:2,reloginPrompts:1,validSessionRestored:true};
  });
  await check('real-download-unwrap-and-failure-behavior-retained',async()=>{
   await download('/system/config/export',{configKey:tag},tag+'.xlsx');assert.equal(masks.at(-1).closed,1);
   const saved=savedFiles.length;assert.ok(saved>0);const blob=savedFiles.at(-1).blob;
   const bytes=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(Buffer.from(reader.result));reader.onerror=reject;reader.readAsArrayBuffer(blob);});assert.equal(bytes.subarray(0,2).toString(),'PK');fs.writeFileSync(dir+'/actual-'+mode+'-export.xlsx',bytes);
   const failed=await outcome(downloadFile({url:'/system/user/2147483646',method:'get'},tag+'.missing.xlsx'));originalError(failed.error,404);assert.equal(savedFiles.length,saved);assert.equal(masks.at(-1).closed,1);
   return {excelBytes:bytes.length,real404:true,noFailureFileSaved:true,loadingReleased:true};
  });
 }finally{
  rules.length=0;
  if(loggedIn){
   const fixtures=(await configs.listConfig({configKey:tag,page:1,pageSize:1000})).items.filter(c=>c.configKey.startsWith(tag+'.'));
   if(fixtures.length)await configs.delConfig(fixtures.map(c=>c.configId).join(','));
   const final=await configs.listConfig({page:1,pageSize:10000});if(initial){assert.deepEqual(final.items,initial.items);assert.equal(final.total,initial.total);}
   results.push({name:'cleanup',ok:true,temporaryConfigsDeleted:fixtures.length,originalConfigsUnchanged:final.items.length,total:final.total});
   await login.logout();auth.removeToken();
  }
  unbindMessage();unbindNotification();dismissReloginPrompt();await new Promise(resolve=>proxy.close(resolve));dom.window.close();
 }
 fs.writeFileSync(dir+'/actual-'+mode+'.json',JSON.stringify({ok:true,mode,evidence:'Production TS modules + Axios XHR + local FastAPI/MySQL. Loopback proxy injects 503 before reads or after a real committed write. UI delivery stubbed; no browser use.',results},null,2));
 console.log(JSON.stringify({ok:true,mode,checks:results.length}));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
