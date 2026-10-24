"""Freeze an identical CRUD task and each version's complete public authoring context."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

evidence = Path(__file__).resolve().parent
previous = evidence.parents[1] / 'schema-enterprise-convergence-2026-10-20' / 'ai-authoring'
cli = Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
sources = {
    'baseline': Path('/var/folders/80/8sfxkvmx2l755p0cgcrkv3740000gn/T/schema-enterprise-baseline-zlt9l0jh/0/packages/schema-form'),
    'current': Path('/Users/hqz/Downloads/element-plus/packages/schema-form'),
}
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
    manifest_path = evidence / 'manifest.json'
    if manifest_path.exists():
        raise SystemExit('Refusing to overwrite a frozen manifest.')
    for name in ('task.md', 'domain.ts', 'output-schema.json'):
        shutil.copyfile(previous / name, evidence / name)
    versions = {}
    for variant, source in sources.items():
        destination = evidence / 'inputs' / variant
        destination.mkdir(parents=True)
        shutil.copyfile(source / 'README.md', destination / 'README.schema-form.md')
        sections = []
        for name in public_files:
            frozen = destination / name
            frozen.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, frozen)
            sections.append(f"### {name}\n```ts\n{frozen.read_text()}```")
        (destination / 'public-types.md').write_text('\n\n'.join(sections) + '\n')
        prompt = (
            (evidence / 'task.md').read_text()
            + '\n\n当前版本README全文：\n\n'
            + (destination / 'README.schema-form.md').read_text()
            + '\n\n当前版本公开入口及类型：\n\n'
            + (destination / 'public-types.md').read_text()
        )
        (destination / 'prompt.md').write_text(prompt)
        versions[variant] = {
            'source': str(source),
            'public_type_files': public_files,
            'prompt_bytes': len(prompt.encode()),
            'prompt_sha256': sha256(destination / 'prompt.md'),
            'readme_sha256': sha256(destination / 'README.schema-form.md'),
            'types_sha256': sha256(destination / 'public-types.md'),
            'source_hashes': {name: sha256(source / name) for name in ['README.md', *public_files]},
        }
    baseline_readme = evidence / 'inputs' / 'baseline' / 'README.schema-form.md'
    if sha256(baseline_readme) != sha256(previous / 'baseline' / 'README.schema-form.md'):
        raise SystemExit('Baseline README differs from the previous frozen snapshot.')
    manifest = {
        'protocol_version': 1,
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'One ordinary Post CRUD task, two independent repetitions per version; no general efficiency claim.',
        'model': 'gpt-6-astra',
        'effort': 'xhigh',
        'cli': str(cli),
        'cli_version': subprocess.check_output([str(cli), '--version'], text=True).strip(),
        'cli_sha256': sha256(cli),
        'timeout_seconds_per_run': 600,
        'sequence': 'ABBA',
        'runs': [
            {'id': '01-baseline', 'variant': 'baseline', 'pair': 1},
            {'id': '02-current', 'variant': 'current', 'pair': 1},
            {'id': '03-current', 'variant': 'current', 'pair': 2},
            {'id': '04-baseline', 'variant': 'baseline', 'pair': 2},
        ],
        'common_hashes': {name: sha256(evidence / name) for name in ('task.md', 'domain.ts', 'output-schema.json')},
        'versions': versions,
        'disabled_features': [
            'shell_tool', 'multi_agent', 'apps', 'plugins', 'hooks', 'memories',
            'browser_use', 'computer_use', 'image_generation', 'view_image',
            'skill_search', 'goals', 'sleep_tool',
        ],
        'enabled_features': ['skip_host_skill_discovery'],
        'config_overrides': {
            'approval_policy': 'never',
            'model_reasoning_effort': 'xhigh',
            'web_search': 'disabled',
            'project_doc_max_bytes': 0,
        },
        'tool_policy': 'No tools. Feature gates reduce available tools; any non-message item invalidates the no-tool protocol.',
        'failure_policy': 'Keep every attempt; no retries, replacement samples, human code edits, or hidden repairs.',
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'manifest': str(manifest_path), 'versions': versions}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
