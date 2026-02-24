#!/usr/bin/env python3
"""Export DI container provider graph."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from container import build_container, validate_container_bindings


def main() -> int:
    parser = argparse.ArgumentParser(description='Export application container dependency graph.')
    parser.add_argument('--format', choices=('dot', 'text'), default='dot')
    parser.add_argument('--output', type=str, default='')
    args = parser.parse_args()

    container = build_container()
    validate_container_bindings(container)
    graph_text = container.export_dependency_graph(output_format=args.format)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(graph_text, encoding='utf-8')
        print(f'Container graph exported: {output_path}')
    else:
        print(graph_text)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
