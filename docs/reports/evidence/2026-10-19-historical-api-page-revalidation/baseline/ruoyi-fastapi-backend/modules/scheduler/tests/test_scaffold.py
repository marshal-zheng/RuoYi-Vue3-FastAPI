"""Scaffold smoke test for modules.scheduler."""

import modules.scheduler.ports as scheduler_ports


def test_scheduler_scaffold_importable() -> None:
    assert scheduler_ports is not None
