import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { chromium } from '/Users/hqz/dev/RuoYi-Vue3-FastAPI/ruoyi-fastapi-frontend/node_modules/@playwright/test/index.mjs';
const bytes=[80,75,3,4,0,255,128];
const browser=await chromium.launch({headless:true});
const page=await browser.newPage();const requests=[];const unexpected=[];const errors=[];
page.on('pageerror',error=>errors.push(error.message));
await page.route(/^http:\/\/127\.0\.0\.1\/api\//,async route=>{
 const request=route.request();const url=new URL(request.url());
 if(url.pathname==='/api/system/protocol/export'){
  requests.push({method:request.method(),contentType:request.headers()['content-type'],body:request.postData()});
  await route.fulfill({status:200,contentType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',body:Buffer.from(bytes)});return;
 }
 unexpected.push({method:request.method(),url:request.url()});await route.abort();
});
await page.route('**/__protocol_export_probe__',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Isolated API transport probe</title>'}));
try{
 await page.goto('http://127.0.0.1/__protocol_export_probe__');
 const result=await page.evaluate(async()=>{
  const {exportProtocol}=await import('/src/api/protocol/protocol.ts');
  const blob=await exportProtocol({protocolId:7});
  return {isBlob:blob instanceof Blob,size:blob.size,type:blob.type,bytes:[...new Uint8Array(await blob.arrayBuffer())]};
 });
 assert.equal(result.isBlob,true);assert.deepEqual(result.bytes,bytes);assert.equal(result.size,bytes.length);
 assert.equal(requests.length,1);assert.equal(requests[0].method,'POST');assert.equal(requests[0].body,'protocolId=7');assert.match(requests[0].contentType,/application\/x-www-form-urlencoded/);
 assert.deepEqual(unexpected,[]);assert.deepEqual(errors,[]);
 const evidence={result,requests,unexpected,errors,browser:browser.version(),scope:'isolated native browser XHR + real API module; network export mocked; no backend writes'};
 await writeFile(new URL('./protocol-export-browser.json',import.meta.url),JSON.stringify(evidence,null,2)+'\n');
 process.stdout.write(JSON.stringify({cases:1,bytesPreserved:true,unexpectedApiRequests:0,pageErrors:0})+'\n');
}finally{await browser.close();}
