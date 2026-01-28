from pathlib import Path

from scripts.check_sensitive_queries import find_violations


def test_sensitive_query_patterns():
    root = Path(__file__).resolve().parents[3]
    violations = find_violations(root)
    assert not violations, f"Sensitive query violations found: {violations}"
