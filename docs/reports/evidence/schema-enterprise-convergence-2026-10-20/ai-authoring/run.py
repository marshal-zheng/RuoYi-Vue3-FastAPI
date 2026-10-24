"""One bounded pair using the existing Codex CLI configuration; no config/auth reads."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

evidence = Path(__file__).resolve().parent
manifest = json.loads((evidence / 'manifest.json').read_text())
cli = '/Users/hqz/.local/bin/codex'
for run in manifest['runs']:
    workspace = Path(run['directory'])
    output = evidence / run['variant']
    args = [
        cli, '--ask-for-approval', 'never', 'exec',
        '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only',
        '--config', 'model_reasoning_effort="xhigh"',
        '--config', 'web_search="disabled"',
        '--json', '--color', 'never', '--cd', str(workspace),
        '--output-schema', str(workspace / 'output-schema.json'),
        '--output-last-message', str(workspace / 'final.json'), '-',
    ]
    started = time.monotonic()
    timed_out = False
    print(f"Starting {run['variant']} (limit 300s)", flush=True)
    with (workspace / 'prompt.md').open('rb') as prompt, \
         (output / 'events.jsonl').open('wb') as events, \
         (output / 'stderr.log').open('wb') as errors:
        process = subprocess.Popen(
            args, stdin=prompt, stdout=events, stderr=errors,
            cwd=workspace, start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
    if (workspace / 'final.json').exists():
        shutil.copyfile(workspace / 'final.json', output / 'final.json')
    events = []
    for line in (output / 'events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    usages = [
        event['usage'] for event in events
        if event.get('type') == 'turn.completed' and 'usage' in event
    ]
    result = {
        'variant': run['variant'], 'command': args,
        'exit_code': exit_code, 'timed_out': timed_out,
        'elapsed_seconds': round(time.monotonic() - started, 3),
        'usage_events': usages,
        'single_turn_usage': usages[0] if len(usages) == 1 else None,
        'event_types': sorted({event.get('type', '') for event in events}),
        'item_types': sorted({
            event['item'].get('type', '') for event in events if 'item' in event
        }),
        'completed': exit_code == 0 and not timed_out and len(usages) == 1,
        'model': manifest['model'], 'effort': manifest['effort'],
    }
    (output / 'run-result.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    )
    print(json.dumps(result, ensure_ascii=False), flush=True)
