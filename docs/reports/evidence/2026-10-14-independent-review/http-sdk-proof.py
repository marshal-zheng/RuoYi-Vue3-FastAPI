from pathlib import Path
import hashlib, json, subprocess, tempfile
root=Path.cwd(); generated=root/'src/api/_generated'; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
logs=[]
def run(args,expected=0):
 p=subprocess.run(args,capture_output=True,text=True)
 logs.append({'args':args,'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 assert p.returncode==expected,(args,p.returncode,p.stderr)
with tempfile.TemporaryDirectory(prefix='independent-sdk-proof-') as directory:
 tmp=Path(directory)
 run(['./node_modules/.bin/openapi-ts','--input','../shared/openapi.json','--output',str(tmp),'--client','@hey-api/client-fetch'])
 run(['node','scripts/postprocess-openapi.mjs',str(tmp)])
 run(['./node_modules/.bin/prettier','--write',str(tmp/'**/*.ts'),'--single-quote','--trailing-comma','es5','--tab-width','2','--semi','--print-width','100'])
 differences=[]; files=[]
 for file in tmp.rglob('*.ts'):
  rel=file.relative_to(tmp); files.append(str(rel))
  if not (generated/rel).exists() or sha(file)!=sha(generated/rel):differences.append(str(rel))
 assert not differences,differences
 owners=[tmp/'client/client.gen.ts',tmp/'client/types.gen.ts',tmp/'core/serverSentEvents.gen.ts']
 first={str(file.relative_to(tmp)):sha(file) for file in owners}
 run(['node','scripts/postprocess-openapi.mjs',str(tmp)])
 second={str(file.relative_to(tmp)):sha(file) for file in owners}
 assert first==second
 changed=owners[-1];changed.write_text(changed.read_text()+'\n// Unreviewed generator change for a rejection control.\n')
 before={str(file.relative_to(tmp)):sha(file) for file in owners}
 run(['node','scripts/postprocess-openapi.mjs',str(tmp)],expected=1)
 after={str(file.relative_to(tmp)):sha(file) for file in owners}
 assert before==after
 report={'filesCompared':sorted(files),'allSourceGeneratedMatches':True,'postprocessIdempotent':True,'unreviewedInputRejected':True,'noPartialWriteOnRejection':True,'normalSourceWrites':0,'commands':logs}
 Path('/tmp/independent-http-sdk-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!='commands'}))
