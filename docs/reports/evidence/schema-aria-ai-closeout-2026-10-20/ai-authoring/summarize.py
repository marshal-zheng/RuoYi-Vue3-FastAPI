"""Audit raw events with the recorded amendment; never modify original results."""
import hashlib
import json
from pathlib import Path
from statistics import mean

evidence = Path(__file__).resolve().parent
manifest = json.loads((evidence / 'manifest.json').read_text())
amendment_path = evidence / 'protocol-amendment-1.json'
amendment = json.loads(amendment_path.read_text())
assert hashlib.sha256(amendment_path.read_bytes()).hexdigest() == '378f63334ed8f808a6ac662477c89f7835f7303bb9ad4dcd2127c24da14fee17'

rows = []
for run in manifest['runs']:
    directory = evidence / 'runs' / run['id']
    result_path = directory / 'run-result.json'
    if not result_path.exists():
        continue
    result = json.loads(result_path.read_text())
    before_turn = True
    exemptions = []
    invalid_events = []
    actual_tool_items = []
    for line_number, line in enumerate((directory / 'events.jsonl').read_text().splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_events.append({'line': line_number, 'reason': 'malformed_jsonl'})
            continue
        if before_turn and event == amendment['exempt_event']:
            exemptions.append({'line': line_number, 'event': event})
            continue
        if event.get('type') == 'turn.started':
            before_turn = False
        item_type = event.get('item', {}).get('type')
        if item_type and item_type not in ('agent_message', 'reasoning'):
            invalid_events.append({'line': line_number, 'event': event})
            if item_type != 'error':
                actual_tool_items.append({'line': line_number, 'event': event})
        elif event.get('type') in ('error', 'turn.failed'):
            invalid_events.append({'line': line_number, 'event': event})
    tokens = result['tokens']
    total = (
        tokens['input_tokens'] + tokens['output_tokens']
        if tokens['input_tokens'] is not None and tokens['output_tokens'] is not None
        else None
    )
    uncached = (
        tokens['input_tokens'] - tokens['cached_input_tokens']
        if tokens['input_tokens'] is not None and tokens['cached_input_tokens'] is not None
        else None
    )
    audit = {
        **run,
        'original_protocol_valid': result['protocol_valid'],
        'original_tool_item_count': result['tool_item_count'],
        'audited_protocol_valid': result['completed'] and not invalid_events,
        'amendment_sha256': hashlib.sha256(amendment_path.read_bytes()).hexdigest(),
        'preflight_warning_exemptions': exemptions,
        'actual_tool_items': actual_tool_items,
        'invalid_events': invalid_events,
        'tokens': tokens,
        'total_tokens': total,
        'uncached_input_tokens': uncached,
        'elapsed_seconds': result['elapsed_seconds'],
        'original_quality_file': f"runs/{run['id']}/quality.json",
        'amended_quality_file': f"runs/{run['id']}/quality-v2.json",
        'manual_review_file': f"runs/{run['id']}/manual-review.md",
    }
    (directory / 'protocol-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    rows.append(audit)

variants = {}
for variant in ('baseline', 'current'):
    selected = [row for row in rows if row['variant'] == variant]
    variants[variant] = {
        'samples_completed': len(selected),
        'audited_protocol_valid_count': sum(row['audited_protocol_valid'] for row in selected),
        'all_samples_retained_in_totals': True,
        'mean_tokens': {
            metric: mean(row['tokens'][metric] for row in selected)
            if selected and all(row['tokens'][metric] is not None for row in selected)
            else None
            for metric in (
                'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens',
            )
        },
        'mean_total_tokens': mean(row['total_tokens'] for row in selected)
        if selected and all(row['total_tokens'] is not None for row in selected) else None,
        'mean_uncached_input_tokens': mean(row['uncached_input_tokens'] for row in selected)
        if selected and all(row['uncached_input_tokens'] is not None for row in selected) else None,
        'mean_elapsed_seconds': mean(row['elapsed_seconds'] for row in selected) if selected else None,
    }
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
        'delta_total_tokens_current_minus_baseline': right['total_tokens'] - left['total_tokens']
        if right['total_tokens'] is not None and left['total_tokens'] is not None else None,
        'delta_tokens_current_minus_baseline': {
            metric: right['tokens'][metric] - left['tokens'][metric]
            if right['tokens'][metric] is not None and left['tokens'][metric] is not None else None
            for metric in (
                'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens',
            )
        },
        'delta_uncached_input_tokens_current_minus_baseline': right['uncached_input_tokens'] - left['uncached_input_tokens']
        if right['uncached_input_tokens'] is not None and left['uncached_input_tokens'] is not None else None,
        'delta_elapsed_seconds_current_minus_baseline': round(right['elapsed_seconds'] - left['elapsed_seconds'], 3),
    })
summary = {
    'scope': manifest['scope'],
    'interpretation': 'Usage describes all attempts. Read independent quality reports before treating any attempt as successful. Reasoning is included in output; do not add it again. Four samples cannot establish general or statistically stable savings.',
    'amendment_sha256': hashlib.sha256(amendment_path.read_bytes()).hexdigest(),
    'samples': rows,
    'variants': variants,
    'pairs': pairs,
    'experiment_totals': {
        'attempts': len(rows),
        'original_protocol_valid_count': sum(row['original_protocol_valid'] for row in rows),
        'audited_protocol_valid_count': sum(row['audited_protocol_valid'] for row in rows),
        'actual_tool_item_count': sum(len(row['actual_tool_items']) for row in rows),
        'preflight_warning_exemption_count': sum(len(row['preflight_warning_exemptions']) for row in rows),
        'tokens': {
            metric: sum(row['tokens'][metric] for row in rows)
            if rows and all(row['tokens'][metric] is not None for row in rows) else None
            for metric in (
                'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens',
            )
        },
        'total_tokens': sum(row['total_tokens'] for row in rows)
        if rows and all(row['total_tokens'] is not None for row in rows) else None,
        'uncached_input_tokens': sum(row['uncached_input_tokens'] for row in rows)
        if rows and all(row['uncached_input_tokens'] is not None for row in rows) else None,
        'elapsed_seconds': round(sum(row['elapsed_seconds'] for row in rows), 3),
        'includes_smoke_test': False,
    },
}
(evidence / 'usage-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({key: summary[key] for key in ('variants', 'pairs', 'experiment_totals')}, ensure_ascii=False, indent=2))
