"""Scaffold smoke test for modules.system."""

import modules.system.ports as system_ports


def test_system_scaffold_importable() -> None:
    assert system_ports is not None
