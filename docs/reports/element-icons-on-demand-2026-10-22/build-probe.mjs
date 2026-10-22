import fs from 'node:fs/promises';
import path from 'node:path';
import { gzipSync } from 'node:zlib';
import { pathToFileURL } from 'node:url';
const { build } = await import(pathToFileURL(path.resolve(process.cwd(), 'node_modules/vite/dist/node/index.js')).href);
const frontend=process.cwd();
const root=path.resolve(frontend,'..');
const known=new Set(JSON.parse(await fs.readFile(path.join(frontend,'src/icons/element-names.json'),'utf8')));
process.env.VITE_ZXUI_LOCAL='true';
process.env.VITE_ZXIO_REPO_ROOT='/Users/hqz/Downloads/element-plus';
const resultFile=path.join(root,'.tmp/element-icons-demand/build-results.json');
const results=JSON.parse(await fs.readFile(resultFile,'utf8').catch(()=>'[]'));
for(const kind of (process.argv[2] ? [process.argv[2]] : ['candidate'])){
  const outDir=path.join(root,'.tmp/element-icons-demand',kind);
  let metrics;
  await build({
    configFile:path.join(frontend,'vite.config.ts'),mode:'production',logLevel:'warn',
    build:{outDir,manifest:true},
    plugins:[{
      name:'task-icon-delivery-evidence',enforce:'pre',
      async load(id){
        if(kind!=='full-registration-control'||id!==path.join(frontend,'src/main.ts'))return null;
        const source=await fs.readFile(id,'utf8');
        const before="import { elementIcons } from '@/icons/element';";
        if(!source.includes(before))throw new Error('Control import no longer matches');
        return source.replace(before,"import * as elementIcons from '@element-plus/icons-vue';");
      },
      generateBundle(_options,bundle){
        const entries=Object.values(bundle).filter(c=>c.type==='chunk'&&c.isEntry);
        const initial=new Set();
        function visit(name){if(initial.has(name))return;const item=bundle[name];if(item?.type!=='chunk')return;initial.add(name);item.imports.forEach(visit);}
        entries.forEach(c=>visit(c.fileName));
        const chunks=[...initial].map(name=>bundle[name]);
        const code=chunks.map(c=>c.code).join('\n');
        const iconNames=[...new Set([...code.matchAll(/\bname\s*:\s*["'](\w+)["']/g)].map(m=>m[1]).filter(n=>known.has(n)))].sort();
        const modules=chunks.flatMap(c=>Object.entries(c.modules).filter(([,m])=>m.renderedLength>0).map(([id,m])=>({id,exports:m.renderedExports})));
        const globalModules=modules.filter(m=>m.id.includes('@element-plus/icons-vue')&&m.id.includes('/global'));
        const allCatalogChunks=Object.values(bundle).filter(c=>c.type==='chunk'&&Object.keys(c.modules).some(id=>id.includes('@element-plus/icons-vue')&&id.includes('/global'))).map(c=>({file:c.fileName,initial:initial.has(c.fileName),raw:c.code.length,gzip:gzipSync(c.code).length}));
        const live=new Set(modules.map(m=>m.id));
        const findPath=(start,target)=>{const queue=[[start]],seen=new Set();while(queue.length){const chain=queue.shift();const id=chain.at(-1);if(id===target)return chain;if(seen.has(id))continue;seen.add(id);for(const child of this.getModuleInfo(id)?.importedIds??[])if(live.has(child))queue.push([...chain,child]);}return null;};
        metrics={kind,sourceLinked:true,initialJsFiles:chunks.length,initialRaw:chunks.reduce((n,c)=>n+Buffer.byteLength(c.code),0),initialGzip:chunks.reduce((n,c)=>n+gzipSync(c.code).length,0),initialIconDefinitions:iconNames.length,iconNames,initialWholeCatalogModules:globalModules,wholeCatalogChunks:allCatalogChunks,initialFiles:[...initial],rootIconExports:modules.filter(m=>m.id.includes('@element-plus/icons-vue')),wholeCatalogImportPaths:globalModules.map(m=>findPath(path.join(frontend,'src/main.ts'),m.id))};
      }
    }]
  });
  if(!metrics)throw new Error('No generated bundle');
  const existing=results.findIndex(r=>r.kind===kind);
  if(existing>=0)results.splice(existing,1);
  results.push(metrics);
  await fs.writeFile(path.join(root,'.tmp/element-icons-demand/build-results.json'),JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify({kind,initialGzip:metrics.initialGzip,iconDefinitions:metrics.initialIconDefinitions,wholeCatalog:metrics.initialWholeCatalogModules.length}));
}
