"""Verify this delivery's tarballs against the installed package files."""

import hashlib
import json
import tarfile
from pathlib import Path

report = Path(__file__).resolve().parent
frontend = report.parents[2] / 'ruoyi-fastapi-frontend'
artifacts = json.loads((report / 'package-identity.json').read_text())
results = []
for artifact in artifacts:
    archive = frontend / artifact['artifact']
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest == artifact['sha256'], archive
    count = 0
    with tarfile.open(archive) as tar:
        for member in tar:
            if not member.isfile():
                continue
            relative = Path(member.name).relative_to('package')
            installed = frontend / 'node_modules' / artifact['name'] / relative
            assert installed.read_bytes() == tar.extractfile(member).read(), installed
            count += 1
    results.append({'name': artifact['name'], 'sha256': digest, 'files': count})
output = {'artifacts': results, 'files': sum(item['files'] for item in results), 'mismatches': 0}
(report / 'installed-files-final.json').write_text(json.dumps(output, indent=2) + '\n')
print(f"{len(results)} packages / {output['files']} files / 0 mismatches")
