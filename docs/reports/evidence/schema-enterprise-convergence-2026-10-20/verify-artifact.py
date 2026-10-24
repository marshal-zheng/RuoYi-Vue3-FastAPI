"""One-off delivery evidence: compare the local package with both consumers."""
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
META = json.loads((HERE / 'artifact.json').read_text())
TARBALL = REPO / 'ruoyi-fastapi-frontend/vendor' / META['filename']
assert hashlib.sha256(TARBALL.read_bytes()).hexdigest() == META['sha256']
with tempfile.TemporaryDirectory(prefix='schema-artifact-check-') as tmp:
    with tarfile.open(TARBALL) as archive:
        archive.extractall(tmp, filter='data')
    package = Path(tmp) / 'package'
    files = [item['path'] for item in META['files']]
    roots = [
        Path('/Users/hqz/Downloads/element-plus/packages/schema-form/dist'),
        REPO / 'ruoyi-fastapi-frontend/node_modules/@zxio/schema-form',
        Path('/Users/hqz/dev/ai/vue-flow/packages/dag/node_modules/@zxio/schema-form'),
    ]
    differences = {str(root): [file for file in files if not (root / file).exists()
                              or (root / file).read_bytes() != (package / file).read_bytes()]
                   for root in roots}
    assert all(not value for value in differences.values()), differences
    manifest = json.loads((package / 'package.json').read_text())
    assert 'source' not in json.dumps(manifest['exports'])
    assert manifest['peerDependenciesMeta']['@form-create/element-ui']['optional']
    imports = {}
    for entry in ['index.mjs', 'fields/index.mjs', 'index.d.ts', 'fields/index.d.ts']:
        todo, seen, external = [package / entry], set(), set()
        while todo:
            path = todo.pop()
            if path in seen:
                continue
            seen.add(path)
            for spec in re.findall(r'''(?:from\s*|import\s*\()['"]([^'"]+)['"]''', path.read_text()):
                if not spec.startswith('.'):
                    external.add(spec)
                    continue
                child = path.parent / spec
                if not child.exists():
                    child = next((p for p in [Path(str(child) + '.d.ts'), child / 'index.d.ts']
                                  if p.exists()), child)
                if child.exists() and child.suffix != '.css':
                    todo.append(child)
        assert not any('@form-create' in item or '.pnpm' in item for item in external), external
        imports[entry] = {'reachableFiles': len(seen), 'externalImports': sorted(external)}
    result = {'tarballSha256': META['sha256'], 'filesComparedPerCopy': len(files),
              'differences': differences, 'rootAndFieldsNoFormCreate': imports,
              'sourceExportRemoved': True, 'optionalFormCreatePeer': True}
(HERE / 'artifact-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
