"""Inspect the real local tarball without installing it into any business."""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import tarfile
from urllib.parse import unquote

evidence = Path(__file__).resolve().parent
zxui = Path('/Users/hqz/Downloads/element-plus')
package = zxui / 'packages/schema-form'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tarball', type=Path)
    args = parser.parse_args()
    with tarfile.open(args.tarball) as archive:
        files = {
            item.name.removeprefix('package/'): archive.extractfile(item).read()
            for item in archive.getmembers() if item.isfile()
        }
    documents = ['README.md', *[
        str(path.relative_to(package))
        for path in sorted((package / 'docs/authoring').glob('*.md'))
    ]]
    links = []
    for name in documents:
        assert name in files, f'Missing document: {name}'
        source_text = (package / name).read_text()
        built_text = files[name].decode()
        # Only link destinations may change during delivery.
        erase_targets = lambda text: re.sub(r'(\]\()([^)\s]+)(\))', r'\1\3', text)
        assert erase_targets(source_text) == erase_targets(built_text), name
        for href in re.findall(r'\]\(([^)\s]+)\)', built_text):
            if re.match(r'^(?:[a-z][a-z\d+.-]*:|#|//)', href, re.I):
                continue
            target = posixpath.normpath(posixpath.join(
                posixpath.dirname(name), unquote(href.split('#', 1)[0])
            ))
            assert target in files, f'Broken installed link: {name} -> {href}'
            links.append({'document': name, 'href': href, 'target': target})
    example_hashes = {}
    pilot = zxui / 'docs/research/schema-form-pilot/pilot'
    for name, data in files.items():
        if name.startswith('examples/'):
            source = pilot / name.removeprefix('examples/')
            assert source.read_bytes() == data, f'Diverged recipe: {name}'
            example_hashes[name] = digest(data)
    baseline = json.loads((evidence / 'baseline.json').read_text())
    for name, expected in baseline['runtime_source_sha256'].items():
        assert digest((zxui / name).read_bytes()) == expected, f'Runtime changed: {name}'
    current_sources = {
        str(p.relative_to(zxui))
        for p in (package / 'src').rglob('*') if p.is_file()
    }
    assert current_sources == set(baseline['runtime_source_sha256']), 'Runtime file set changed'
    result = {
        'status': 'passed',
        'tarball': str(args.tarball.resolve()),
        'tarball_sha256': digest(args.tarball.read_bytes()),
        'documents': documents,
        'local_links': links,
        'example_sha256': example_hashes,
        'unchanged_runtime_source_count': len(current_sources),
        'published_manifest': json.loads(files['package.json']),
        'limits': ['Checks local link targets, not browser rendering or external URLs.'],
    }
    (evidence / 'package-verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    )
    print(json.dumps({
        'status': result['status'], 'documents': len(documents),
        'resolved_local_links': len(links), 'identical_recipes': len(example_hashes),
        'unchanged_runtime_sources': len(current_sources),
        'tarball_sha256': result['tarball_sha256'],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
