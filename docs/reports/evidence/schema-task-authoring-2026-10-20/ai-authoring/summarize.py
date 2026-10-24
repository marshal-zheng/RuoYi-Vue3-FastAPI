"""Recompute descriptive usage totals from untouched formal run records."""
import hashlib
import json
from pathlib import Path
from statistics import mean

evidence = Path(__file__).resolve().parent
manifest = json.loads((evidence / 'manifest.json').read_text())
metrics = (
    'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
    'output_tokens', 'reasoning_output_tokens',
)
rows = []
for run in manifest['runs']:
    directory = evidence / 'runs' / run['id']
    if not (directory / 'run-result.json').exists():
        continue
    result = json.loads((directory / 'run-result.json').read_text())
    for name, expected in result['raw_sha256'].items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == expected
    tokens = result['tokens']
    rows.append({
        **run,
        'label': manifest['versions'][run['variant']]['label'],
        'protocol_valid': result['protocol_valid'],
        'tool_item_count': result['tool_item_count'],
        'allowed_preflight_warning_count': len(result['preflight_warnings']),
        'completed': result['completed'],
        'exit_code': result['exit_code'],
        'timed_out': result['timed_out'],
        'tokens': tokens,
        'total_tokens': tokens['input_tokens'] + tokens['output_tokens']
        if tokens['input_tokens'] is not None and tokens['output_tokens'] is not None else None,
        'uncached_input_tokens': tokens['input_tokens'] - tokens['cached_input_tokens']
        if tokens['input_tokens'] is not None and tokens['cached_input_tokens'] is not None else None,
        'elapsed_seconds': result['elapsed_seconds'],
        'quality_file': f"runs/{run['id']}/quality.json",
        'manual_review_file': f"runs/{run['id']}/manual-review.md",
    })


def aggregate(values, operation):
    return operation(values) if values and all(value is not None for value in values) else None


variants = {}
for variant in ('baseline', 'current'):
    selected = [row for row in rows if row['variant'] == variant]
    variants[variant] = {
        'label': manifest['versions'][variant]['label'],
        'attempts_recorded': len(selected),
        'completed_count': sum(row['completed'] for row in selected),
        'protocol_valid_count': sum(row['protocol_valid'] for row in selected),
        'all_attempts_retained': True,
        'mean_tokens': {
            metric: aggregate([row['tokens'][metric] for row in selected], mean)
            for metric in metrics
        },
        'mean_total_tokens': aggregate([row['total_tokens'] for row in selected], mean),
        'mean_uncached_input_tokens': aggregate([row['uncached_input_tokens'] for row in selected], mean),
        'mean_elapsed_seconds': aggregate([row['elapsed_seconds'] for row in selected], mean),
    }


def subtract(right, left):
    return right - left if right is not None and left is not None else None


pairs = []
for pair in (1, 2):
    selected = {row['variant']: row for row in rows if row['pair'] == pair}
    if set(selected) != {'baseline', 'current'}:
        continue
    left, right = selected['baseline'], selected['current']
    pairs.append({
        'pair': pair,
        'baseline': left['id'],
        'current': right['id'],
        'delta_tokens_current_minus_baseline': {
            metric: subtract(right['tokens'][metric], left['tokens'][metric])
            for metric in metrics
        },
        'delta_total_tokens_current_minus_baseline': subtract(right['total_tokens'], left['total_tokens']),
        'delta_uncached_input_tokens_current_minus_baseline': subtract(right['uncached_input_tokens'], left['uncached_input_tokens']),
        'delta_elapsed_seconds_current_minus_baseline': round(right['elapsed_seconds'] - left['elapsed_seconds'], 3),
    })
summary = {
    'scope': manifest['scope'],
    'cost_scope': 'Usage covers only the four controlled single-turn code-authoring model calls (input + output). It excludes engineering/documentation work, independent quality-check and human-review agent tokens, previous experiments, smoke runs, and retrieval/routing. It is not complete development-workflow consumption.',
    'interpretation': 'Compare the supplied documentation combinations/content for one preselected ordinary CRUD task. Do not separate content/organization/length effects or generalize to retrieval, full AI development, or stable reasoning/latency improvements. Read independent quality outcomes before treating a generation as successful. Reasoning is already included in output.',
    'samples': rows,
    'variants': variants,
    'pairs': pairs,
    'experiment_totals': {
        'attempts': len(rows),
        'completed_count': sum(row['completed'] for row in rows),
        'protocol_valid_count': sum(row['protocol_valid'] for row in rows),
        'tool_item_count': sum(row['tool_item_count'] for row in rows),
        'allowed_preflight_warning_count': sum(row['allowed_preflight_warning_count'] for row in rows),
        'tokens': {
            metric: aggregate([row['tokens'][metric] for row in rows], sum)
            for metric in metrics
        },
        'total_tokens': aggregate([row['total_tokens'] for row in rows], sum),
        'uncached_input_tokens': aggregate([row['uncached_input_tokens'] for row in rows], sum),
        'elapsed_seconds': round(sum(row['elapsed_seconds'] for row in rows), 3),
        'includes_prior_experiments_or_smoke': False,
    },
}
(evidence / 'usage-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: summary[key] for key in ('variants', 'pairs', 'experiment_totals')}, ensure_ascii=False, indent=2))
