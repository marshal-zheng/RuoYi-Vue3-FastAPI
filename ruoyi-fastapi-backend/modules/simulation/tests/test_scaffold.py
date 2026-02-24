"""Scaffold smoke test for modules.simulation."""

import modules.simulation.ports as simulation_ports


def test_simulation_scaffold_importable() -> None:
    assert simulation_ports is not None
