"""Run the frozen ABBA protocol; raw responses and usage are never edited."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

evidence = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(manifest):
    for name, expected in manifest['common_hashes'].items():
        if sha256(evidence / name) != expected:
            raise RuntimeError(f'Frozen common file changed: {name}')
    for variant, details in manifest['versions'].items():
        inputs = evidence / 'inputs' / variant
        for name, key in (
            ('prompt.md', 'prompt_sha256'),
            ('README.schema-form.md', 'readme_sha256'),
            ('public-types.md', 'types_sha256'),
        ):
            if sha256(inputs / name) != details[key]:
                raise RuntimeError(f'Frozen input changed: {variant}/{name}')
        for name, expected in details['source_hashes'].items():
            frozen = inputs / ('README.schema-form.md' if name == 'README.md' else name)
            if sha256(frozen) != expected:
                raise RuntimeError(f'Frozen source changed: {variant}/{name}')
    cli = Path(manifest['cli'])
    if sha256(cli) != manifest['cli_sha256']:
        raise RuntimeError('CLI binary changed after protocol freeze.')


def verify_checker():
    freeze_path = evidence / 'checker' / 'freeze.json'
    if not freeze_path.exists():
        raise RuntimeError('Independent quality checker must be frozen before model calls.')
    freeze = json.loads(freeze_path.read_text())
    if freeze.get('oracle_status') != 'passed':
        raise RuntimeError('Quality checker has not passed its oracle validation.')
    for name, expected in freeze['files'].items():
        if sha256(evidence / name) != expected:
            raise RuntimeError(f'Frozen checker changed: {name}')


def arguments(manifest, workspace, output):
    args = [
        manifest['cli'], 'exec',
        '--ignore-user-config', '--ignore-rules',
        '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only',
        '--model', manifest['model'],
        '--json', '--color', 'never', '--cd', str(workspace),
        '--output-schema', str(evidence / 'output-schema.json'),
        '--output-last-message', str(output / 'final.json'),
    ]
    for key, value in manifest['config_overrides'].items():
        # These strings are CLI argv values, never evaluated by a shell.
        args.extend(['--config', f'{key}={json.dumps(value)}'])
    for name in manifest['disabled_features']:
        args.extend(['--disable', name])
    for name in manifest['enabled_features']:
        args.extend(['--enable', name])
    args.append('-')
    return args


def run_one(manifest, run):
    output = evidence / 'runs' / run['id']
    output.mkdir(parents=True, exist_ok=False)
    workspace = Path(tempfile.mkdtemp(prefix='schema-ai-authoring-'))
    args = arguments(manifest, workspace, output)
    prompt_path = evidence / 'inputs' / run['variant'] / 'prompt.md'
    started_at = datetime.now(timezone.utc).isoformat()
    (output / 'command.json').write_text(json.dumps(args, ensure_ascii=False, indent=2) + '\n')
    (output / 'invocation.json').write_text(json.dumps({
        **run,
        'workspace': str(workspace),
        'workspace_initial_contents': list(workspace.iterdir()),
        'started_at_utc': started_at,
        'prompt_sha256': sha256(prompt_path),
        'cli_sha256': manifest['cli_sha256'],
        'manifest_sha256': sha256(evidence / 'manifest.json'),
        'protocol_sha256': sha256(evidence / 'protocol.md'),
        'runner_sha256': sha256(Path(__file__)),
        'checker_freeze_sha256': sha256(evidence / 'checker' / 'freeze.json'),
    }, ensure_ascii=False, indent=2) + '\n')
    started = time.monotonic()
    timed_out = False
    print(f"Starting {run['id']} (limit {manifest['timeout_seconds_per_run']}s)", flush=True)
    with prompt_path.open('rb') as prompt, (output / 'events.jsonl').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
        process = subprocess.Popen(
            args, stdin=prompt, stdout=stdout, stderr=stderr,
            cwd=workspace, start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=manifest['timeout_seconds_per_run'])
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
    events = []
    malformed_lines = []
    for number, line in enumerate((output / 'events.jsonl').read_text().splitlines(), 1):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed_lines.append(number)
    usages = [event['usage'] for event in events if event.get('type') == 'turn.completed' and 'usage' in event]
    item_types = sorted({event['item'].get('type', '') for event in events if 'item' in event})
    tool_items = [event for event in events if 'item' in event and event['item'].get('type') not in ('agent_message', 'reasoning')]
    parsed_final = None
    final_schema_valid = False
    if (output / 'final.json').exists():
        try:
            parsed_final = json.loads((output / 'final.json').read_text())
            final_schema_valid = (
                isinstance(parsed_final, dict)
                and set(parsed_final) == {'postFormTs', 'postEditorVue'}
                and all(isinstance(value, str) for value in parsed_final.values())
            )
        except json.JSONDecodeError:
            pass
    completed = exit_code == 0 and not timed_out and len(usages) == 1 and final_schema_valid
    valid = completed and not malformed_lines and not tool_items
    usage = usages[0] if len(usages) == 1 else {}
    result = {
        **run,
        'command': args,
        'workspace': str(workspace),
        'started_at_utc': started_at,
        'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'exit_code': exit_code,
        'timed_out': timed_out,
        'elapsed_seconds': round(time.monotonic() - started, 3),
        'usage_events': usages,
        'single_turn_usage': usages[0] if len(usages) == 1 else None,
        'tokens': {
            key: usage.get(key) for key in (
                'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens',
            )
        },
        'event_types': sorted({event.get('type', '') for event in events}),
        'item_types': item_types,
        'tool_item_count': len(tool_items),
        'malformed_jsonl_lines': malformed_lines,
        'final_schema_valid': final_schema_valid,
        'completed': completed,
        'protocol_valid': valid,
        'model': manifest['model'],
        'effort': manifest['effort'],
        'quality_check': {'status': 'pending_independent_validation'},
        'raw_sha256': {
            name: sha256(output / name) for name in ('events.jsonl', 'stderr.log', 'final.json')
            if (output / name).exists()
        },
    }
    (output / 'run-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('id', 'exit_code', 'elapsed_seconds', 'tokens', 'protocol_valid')}, ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true', help='Run the frozen model calls; otherwise only verify inputs.')
    args = parser.parse_args()
    manifest = json.loads((evidence / 'manifest.json').read_text())
    verify_inputs(manifest)
    if not args.execute:
        print(json.dumps({'status': 'prepared_not_run', 'run_order': [run['id'] for run in manifest['runs']]}, indent=2))
        return
    if (evidence / 'runs').exists():
        raise SystemExit('Refusing to replace or retry prior attempts in this frozen experiment.')
    verify_checker()
    results = [run_one(manifest, run) for run in manifest['runs']]
    (evidence / 'run-summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
