"""Freeze a documentation-only comparison; never invoke a model."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

evidence = Path(__file__).resolve().parent
source = Path('/Users/hqz/Downloads/element-plus/packages/schema-form')
public_files = [
    'src/index.ts',
    'src/types.ts',
    'src/form-create/index.ts',
    'src/form-create/types.ts',
    'src/fields/types.ts',
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (evidence / 'manifest.json').exists():
        raise SystemExit('Refusing to overwrite the frozen experiment.')
    baseline = json.loads((evidence / 'baseline-freeze.json').read_text())
    for name, expected in {**baseline['files'], **baseline['common_files']}.items():
        assert sha256(evidence / name) == expected, f'Baseline/common input changed: {name}'
    settings = json.loads((evidence / 'runtime-settings.json').read_text())
    assert sha256(Path(settings['cli'])) == settings['cli_sha256'], 'CLI changed'
    for name in public_files:
        assert sha256(source / name) == sha256(evidence / 'inputs/baseline' / name), f'API changed: {name}'
    destination = evidence / 'inputs/current'
    if destination.exists():
        raise SystemExit('Current inputs already exist; review them instead of replacing.')
    destination.mkdir(parents=True)
    for name in ['README.md', 'docs/authoring/crud.md', *public_files]:
        frozen = destination / name
        frozen.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, frozen)
    versions = {}
    for variant, document_names in (
        ('baseline', ['README.md']),
        ('current', ['README.md', 'docs/authoring/crud.md']),
    ):
        inputs = evidence / 'inputs' / variant
        sections = [
            f"### {name}\n```ts\n{(inputs / name).read_text()}```"
            for name in public_files
        ]
        (inputs / 'public-types.md').write_text('\n\n'.join(sections) + '\n')
        docs = '\n\n'.join(
            f"### {name}\n\n{(inputs / name).read_text()}"
            for name in document_names
        )
        prompt = (
            (evidence / 'task.md').read_text()
            + '\n\n本次提供的公开作者文档全文：\n\n'
            + docs
            + '\n\n当前版本公开入口及类型：\n\n'
            + (inputs / 'public-types.md').read_text()
        )
        (inputs / 'prompt.md').write_text(prompt)
        versions[variant] = {
            'label': 'full docs' if variant == 'baseline' else 'task docs',
            'source_documents': document_names,
            'public_type_files': public_files,
            'prompt_bytes': len(prompt.encode()),
            'prompt_sha256': sha256(inputs / 'prompt.md'),
            'types_sha256': sha256(inputs / 'public-types.md'),
            'document_sha256': {name: sha256(inputs / name) for name in document_names},
        }
    assert versions['baseline']['types_sha256'] == versions['current']['types_sha256']
    checker = json.loads((evidence / 'checker/freeze.json').read_text())
    assert checker['oracle_status'] == 'passed'
    for name, expected in checker['files'].items():
        assert sha256(evidence / name) == expected, f'Checker changed: {name}'
    frozen_names = [
        'baseline-freeze.json', 'runtime-settings.json', 'task.md', 'domain.ts',
        'output-schema.json', 'artifacts.json', 'protocol.md', 'prepare.py',
        'run.py', 'checker/freeze.json', *checker['files'],
    ]
    frozen_names += [
        str(path.relative_to(evidence))
        for path in sorted((evidence / 'inputs').rglob('*'))
        if path.is_file()
    ]
    manifest = {
        'protocol_version': 1,
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'One ordinary Post CRUD authoring task with preselected materials, two repetitions per group; same current schema API/artifact. Compare full documentation with task documentation content and organization, not retrieval costs or the complete AI development workflow.',
        **settings,
        'sequence': 'ABBA',
        'runs': [
            {'id': '01-baseline', 'variant': 'baseline', 'pair': 1},
            {'id': '02-current', 'variant': 'current', 'pair': 1},
            {'id': '03-current', 'variant': 'current', 'pair': 2},
            {'id': '04-baseline', 'variant': 'baseline', 'pair': 2},
        ],
        'versions': versions,
        'frozen_files': {name: sha256(evidence / name) for name in frozen_names},
        'same_public_types': True,
        'shared_artifact_archive_sha256': json.loads((evidence / 'artifacts.json').read_text())['archive_sha256'],
        'quality_rule': 'Use the current API checker for BOTH groups; baseline means full documentation, never the historical schema API.',
        'warning_rule': 'Only a complete event exactly equal to allowed_preflight_warning before the first turn.started is a client warning, not a tool call. Every other error/tool item invalidates the run.',
        'failure_policy': 'Keep every attempt; no model retries, replacement samples, human code edits, or hidden repairs.',
    }
    (evidence / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'frozen_not_run', 'versions': versions}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
